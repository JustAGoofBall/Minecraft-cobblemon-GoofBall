import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.UncheckedIOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * Server launcher for the GoofBall Cobblemon modpack.
 *
 * <p>On every start it makes the server folder match the modpack version this jar was built for:
 * it downloads missing or changed mods from the Modrinth CDN (sha512-checked), removes mods it
 * installed earlier that are no longer in the pack, and copies default configs that don't exist
 * yet. Then it starts Fabric (fabric-server-launch.jar, on the manifest Class-Path) in this same
 * JVM, so console input, "stop" and the JVM memory flags work exactly as with a normal server jar.
 *
 * <p>Embedded resources (written by scripts/build_server.py):
 * <ul>
 *   <li>{@code goofball/pack.properties} - name and version of the pack</li>
 *   <li>{@code goofball/files.tsv} - one server file per line: path, sha512, size, url[, url...]</li>
 *   <li>{@code goofball/overrides.txt} + {@code goofball/overrides/...} - default config files</li>
 * </ul>
 *
 * <p>Set {@code -Dgoofball.skipSync=true} to start without checking or downloading mods.
 */
public final class GoofBallServer {
    private static final Path ROOT = Path.of("").toAbsolutePath().normalize();
    private static final Path STATE_FILE = ROOT.resolve(".goofball").resolve("installed.tsv");
    private static final int DOWNLOAD_THREADS = 6;
    private static final int ATTEMPTS_PER_URL = 3;
    private static final String USER_AGENT =
            "JustAGoofBall/Minecraft-cobblemon-GoofBall goofball-server (github.com/JustAGoofBall/Minecraft-cobblemon-GoofBall)";

    private record PackFile(String path, String sha512, long size, List<String> urls) {}

    public static void main(String[] args) throws Throwable {
        Properties pack = new Properties();
        try (InputStream in = resource("pack.properties")) {
            pack.load(in);
        }
        log("%s %s", pack.getProperty("name"), pack.getProperty("version"));

        if (Boolean.getBoolean("goofball.skipSync")) {
            log("goofball.skipSync=true, not checking mods");
        } else if (!sync()) {
            log("Not starting the server because some files could not be downloaded. See the errors above.");
            log("Check the internet connection of the server, then start it again.");
            System.exit(1);
        }

        Class<?> fabric;
        try {
            fabric = Class.forName("net.fabricmc.installer.ServerLauncher");
        } catch (ClassNotFoundException e) {
            log("fabric-server-launch.jar is missing. Put it next to goofball-server.jar (it is in the server zip).");
            System.exit(1);
            return;
        }
        log("Starting Fabric server");
        fabric.getMethod("main", String[].class).invoke(null, (Object) args);
    }

    /** Brings the server folder in line with the pack. Returns false if a download failed. */
    private static boolean sync() throws IOException, InterruptedException {
        Map<String, PackFile> wanted = readPackFiles();
        Map<String, String> installed = readState();

        // Remove files this launcher installed earlier that are no longer part of the pack.
        for (String path : installed.keySet()) {
            if (!wanted.containsKey(path) && Files.deleteIfExists(safeResolve(path))) {
                log("Removed %s (no longer in the pack)", path);
            }
        }

        List<PackFile> missing = new ArrayList<>();
        for (PackFile file : wanted.values()) {
            Path target = safeResolve(file.path());
            boolean known = file.sha512().equals(installed.get(file.path()));
            if (Files.isRegularFile(target)
                    && Files.size(target) == file.size()
                    && (known || file.sha512().equals(sha512(target)))) {
                continue;
            }
            missing.add(file);
        }

        Map<String, String> newState = new LinkedHashMap<>();
        boolean ok = true;
        if (missing.isEmpty()) {
            log("All %d mods are up to date", wanted.size());
        } else {
            log("Downloading %d of %d files from Modrinth...", missing.size(), wanted.size());
            HttpClient http = HttpClient.newBuilder()
                    .followRedirects(HttpClient.Redirect.NORMAL)
                    .connectTimeout(Duration.ofSeconds(30))
                    .build();
            ExecutorService pool = Executors.newFixedThreadPool(DOWNLOAD_THREADS);
            try {
                List<Future<Boolean>> results = new ArrayList<>();
                for (PackFile file : missing) {
                    results.add(pool.submit(() -> download(http, file)));
                }
                for (Future<Boolean> result : results) {
                    try {
                        ok &= result.get();
                    } catch (Exception e) {
                        log("Download error: %s", e);
                        ok = false;
                    }
                }
            } finally {
                pool.shutdown();
            }
        }

        // Record every wanted file that is now present and correct.
        for (PackFile file : wanted.values()) {
            Path target = safeResolve(file.path());
            if (Files.isRegularFile(target) && Files.size(target) == file.size()) {
                newState.put(file.path(), file.sha512());
            }
        }
        writeState(newState);
        copyOverrides();
        return ok;
    }

    private static boolean download(HttpClient http, PackFile file) throws IOException, InterruptedException {
        Path target = safeResolve(file.path());
        Files.createDirectories(target.getParent());
        Path tmp = target.resolveSibling(target.getFileName() + ".part");
        for (String url : file.urls()) {
            for (int attempt = 1; attempt <= ATTEMPTS_PER_URL; attempt++) {
                try {
                    HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                            .header("User-Agent", USER_AGENT)
                            .timeout(Duration.ofMinutes(5))
                            .build();
                    HttpResponse<InputStream> response = http.send(request, HttpResponse.BodyHandlers.ofInputStream());
                    if (response.statusCode() != 200) {
                        response.body().close();
                        throw new IOException("HTTP " + response.statusCode());
                    }
                    MessageDigest digest = newSha512();
                    try (InputStream in = new DigestInputStream(response.body(), digest);
                         OutputStream out = Files.newOutputStream(tmp)) {
                        in.transferTo(out);
                    }
                    String hash = HexFormat.of().formatHex(digest.digest());
                    if (!hash.equals(file.sha512())) {
                        throw new IOException("sha512 mismatch");
                    }
                    Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
                    log("Downloaded %s", file.path());
                    return true;
                } catch (IOException e) {
                    Files.deleteIfExists(tmp);
                    log("Attempt %d for %s failed (%s): %s", attempt, file.path(), e.getMessage(), url);
                    Thread.sleep(2000L * attempt);
                }
            }
        }
        log("ERROR: could not download %s", file.path());
        return false;
    }

    /** Default configs: only written when the file doesn't exist, so server edits are kept. */
    private static void copyOverrides() throws IOException {
        for (String path : readLines("overrides.txt")) {
            Path target = safeResolve(path);
            if (Files.exists(target)) {
                continue;
            }
            Files.createDirectories(target.getParent());
            try (InputStream in = resource("overrides/" + path)) {
                Files.copy(in, target);
            }
            log("Added default %s", path);
        }
    }

    private static Map<String, PackFile> readPackFiles() throws IOException {
        Map<String, PackFile> files = new LinkedHashMap<>();
        for (String line : readLines("files.tsv")) {
            String[] parts = line.split("\t");
            List<String> urls = List.of(parts).subList(3, parts.length);
            files.put(parts[0], new PackFile(parts[0], parts[1], Long.parseLong(parts[2]), urls));
        }
        return files;
    }

    private static Map<String, String> readState() throws IOException {
        Map<String, String> state = new LinkedHashMap<>();
        if (Files.exists(STATE_FILE)) {
            for (String line : Files.readAllLines(STATE_FILE, StandardCharsets.UTF_8)) {
                String[] parts = line.split("\t");
                if (parts.length == 2) {
                    state.put(parts[0], parts[1]);
                }
            }
        }
        return state;
    }

    private static void writeState(Map<String, String> state) throws IOException {
        Files.createDirectories(STATE_FILE.getParent());
        StringBuilder text = new StringBuilder();
        state.forEach((path, hash) -> text.append(path).append('\t').append(hash).append('\n'));
        Path tmp = STATE_FILE.resolveSibling("installed.tsv.tmp");
        Files.writeString(tmp, text, StandardCharsets.UTF_8);
        Files.move(tmp, STATE_FILE, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
    }

    /** Resolves a pack path inside the server folder; rejects absolute paths and "..". */
    private static Path safeResolve(String path) {
        Path resolved = ROOT.resolve(path).normalize();
        if (!resolved.startsWith(ROOT) || resolved.equals(ROOT)) {
            throw new IllegalArgumentException("Unsafe path in modpack: " + path);
        }
        return resolved;
    }

    private static String sha512(Path file) throws IOException {
        MessageDigest digest = newSha512();
        try (InputStream in = new DigestInputStream(Files.newInputStream(file), digest)) {
            in.transferTo(OutputStream.nullOutputStream());
        }
        return HexFormat.of().formatHex(digest.digest());
    }

    private static MessageDigest newSha512() {
        try {
            return MessageDigest.getInstance("SHA-512");
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }

    private static List<String> readLines(String name) throws IOException {
        try (InputStream in = resource(name)) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8).lines().filter(l -> !l.isBlank()).toList();
        }
    }

    private static InputStream resource(String name) throws IOException {
        InputStream in = GoofBallServer.class.getResourceAsStream("/goofball/" + name);
        if (in == null) {
            throw new UncheckedIOException(new IOException("Missing resource goofball/" + name + " in goofball-server.jar"));
        }
        return in;
    }

    private static void log(String format, Object... args) {
        System.out.println("[GoofBall] " + String.format(format, args));
    }
}
