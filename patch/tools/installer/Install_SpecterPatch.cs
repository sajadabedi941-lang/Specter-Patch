// Specter Ultimate Expansion — standalone BIG installer (Windows .NET)
// Compiled with: mcs -sdk:4 -r:System.Windows.Forms.dll -r:System.Drawing.dll -out:Install_SpecterPatch.exe Install_SpecterPatch.cs
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace SpecterUltimateInstaller
{
    static class Program
    {
        const string AppName = "Specter Ultimate Expansion";
        const string DataBig = "_SPEC_DATA_ONE.big";
        const string ArtBig = "_SPEC_ART_ONE.big";
        const string MarkerName = "SPECTER_ULTIMATE_EXPANSION_INSTALLED.txt";
        const string RootPathFile = "SpecterGameRoot.path";

        [STAThread]
        static int Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            Console.OutputEncoding = Encoding.UTF8;
            Banner();

            string srcDir = AppDomain.CurrentDomain.BaseDirectory;
            if (string.IsNullOrEmpty(srcDir))
                srcDir = Path.GetDirectoryName(Application.ExecutablePath) ?? ".";
            srcDir = Path.GetFullPath(srcDir.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar));

            string dataSrc = Path.Combine(srcDir, DataBig);
            string artSrc = Path.Combine(srcDir, ArtBig);

            if (!File.Exists(dataSrc) || !File.Exists(artSrc))
            {
                Fail("BIG files not found next to Install_SpecterPatch.exe.\nExpected:\n  " + dataSrc + "\n  " + artSrc);
                return 1;
            }

            string gameRoot = null;
            if (args != null && args.Length > 0 && !string.IsNullOrWhiteSpace(args[0]))
                gameRoot = args[0].Trim().Trim('"');

            if (!IsGameRoot(gameRoot))
                gameRoot = AutoDetectGameRoot(srcDir);

            if (!IsGameRoot(gameRoot))
                gameRoot = AskGameRoot(srcDir);

            if (!IsGameRoot(gameRoot))
            {
                Fail("No valid Specter GameRoot selected.\nGameRoot must contain generals.exe (or Generals.exe) and usually a Data folder.");
                return 1;
            }

            Console.WriteLine("GameRoot: " + gameRoot);
            Console.WriteLine("Source:   " + srcDir);
            Console.WriteLine();

            try
            {
                string stamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string backup = Path.Combine(gameRoot, "SpecterBIG_Backup_" + stamp);
                Directory.CreateDirectory(backup);

                Console.WriteLine("[1/4] Backing up existing BIG files...");
                BackupIfExists(Path.Combine(gameRoot, DataBig), Path.Combine(backup, DataBig));
                BackupIfExists(Path.Combine(gameRoot, ArtBig), Path.Combine(backup, ArtBig));
                Console.WriteLine("  Backup folder: " + backup);
                Console.WriteLine();

                Console.WriteLine("[2/4] Installing new BIG files...");
                File.Copy(dataSrc, Path.Combine(gameRoot, DataBig), true);
                Console.WriteLine("  Installed " + DataBig);
                File.Copy(artSrc, Path.Combine(gameRoot, ArtBig), true);
                Console.WriteLine("  Installed " + ArtBig);
                Console.WriteLine();

                Console.WriteLine("[3/4] Writing install marker + GameRoot path...");
                File.WriteAllText(Path.Combine(gameRoot, MarkerName),
                    AppName + " installed.\r\nInstalledAt=" + DateTime.Now.ToString("u") + "\r\nGameRoot=" + gameRoot + "\r\nBackup=" + backup + "\r\n");
                File.WriteAllText(Path.Combine(srcDir, RootPathFile), gameRoot + "\r\n");
                try
                {
                    string appData = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SpecterUltimateExpansion");
                    Directory.CreateDirectory(appData);
                    File.WriteAllText(Path.Combine(appData, RootPathFile), gameRoot + "\r\n");
                }
                catch { /* optional */ }

                Console.WriteLine("[4/4] Creating desktop shortcut...");
                string exePath = FindGeneralsExe(gameRoot);
                string shortcutPath = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),
                    AppName + ".lnk");
                CreateShortcut(shortcutPath, exePath, gameRoot,
                    "Launch Command & Conquer Generals Zero Hour Specter (Ultimate Expansion)");
                Console.WriteLine("  Shortcut: " + shortcutPath);
                Console.WriteLine();

                Console.WriteLine("============================================================");
                Console.WriteLine(" INSTALLATION COMPLETED SUCCESSFULLY");
                Console.WriteLine("============================================================");
                Console.WriteLine();
                Console.WriteLine(" Installed:");
                Console.WriteLine("   " + Path.Combine(gameRoot, DataBig));
                Console.WriteLine("   " + Path.Combine(gameRoot, ArtBig));
                Console.WriteLine(" Backup:");
                Console.WriteLine("   " + backup);
                Console.WriteLine();

                DialogResult launch = MessageBox.Show(
                    "Installation completed successfully.\n\nLaunch Specter now?",
                    AppName,
                    MessageBoxButtons.YesNo,
                    MessageBoxIcon.Information);

                if (launch == DialogResult.Yes)
                {
                    try
                    {
                        Process.Start(new ProcessStartInfo
                        {
                            FileName = exePath,
                            WorkingDirectory = gameRoot,
                            UseShellExecute = true
                        });
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Could not launch generals.exe:\n" + ex.Message, AppName, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                }
                return 0;
            }
            catch (Exception ex)
            {
                Fail("Installation failed:\n" + ex.Message);
                return 1;
            }
        }

        static void Banner()
        {
            Console.WriteLine();
            Console.WriteLine("============================================================");
            Console.WriteLine(" SPECTER ULTIMATE EXPANSION INSTALLER");
            Console.WriteLine(" Automatic playable BIG installer");
            Console.WriteLine("============================================================");
            Console.WriteLine();
        }

        static void Fail(string msg)
        {
            Console.WriteLine();
            Console.WriteLine("ERROR: " + msg);
            try { MessageBox.Show(msg, AppName + " — Error", MessageBoxButtons.OK, MessageBoxIcon.Error); }
            catch { }
            Console.WriteLine();
            Console.WriteLine("Press Enter to exit...");
            try { Console.ReadLine(); } catch { }
        }

        static void BackupIfExists(string src, string dst)
        {
            if (File.Exists(src))
            {
                File.Copy(src, dst, true);
                Console.WriteLine("  Backed up " + Path.GetFileName(src));
            }
        }

        static bool IsGameRoot(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) return false;
            try
            {
                if (!Directory.Exists(path)) return false;
                if (FindGeneralsExe(path) == null) return false;
                // Prefer roots that already have Specter BIGs or a Data folder, but exe alone is enough
                return true;
            }
            catch { return false; }
        }

        static string FindGeneralsExe(string root)
        {
            string[] names = { "generals.exe", "Generals.exe", "GeneralsZH.exe", "generalszh.exe" };
            foreach (string n in names)
            {
                string p = Path.Combine(root, n);
                if (File.Exists(p)) return p;
            }
            return null;
        }

        static string AutoDetectGameRoot(string srcDir)
        {
            Console.WriteLine("Detecting Specter GameRoot...");

            // 1) Installer folder itself
            if (IsGameRoot(srcDir)) return Path.GetFullPath(srcDir);

            // 2) Walk parents
            try
            {
                var dir = new DirectoryInfo(srcDir);
                for (int i = 0; i < 5 && dir != null; i++)
                {
                    if (IsGameRoot(dir.FullName)) return dir.FullName;
                    dir = dir.Parent;
                }
            }
            catch { }

            // 3) Saved path from prior install
            string[] saved = {
                Path.Combine(srcDir, RootPathFile),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SpecterUltimateExpansion", RootPathFile)
            };
            foreach (string s in saved)
            {
                try
                {
                    if (File.Exists(s))
                    {
                        string line = File.ReadAllText(s).Trim().Split('\r', '\n')[0].Trim().Trim('"');
                        if (IsGameRoot(line)) return line;
                    }
                }
                catch { }
            }

            // 4) Common install locations / drives
            string[] bases = {
                @"C:\Program Files\EA Games\Command & Conquer Generals Zero Hour",
                @"C:\Program Files (x86)\EA Games\Command & Conquer Generals Zero Hour",
                @"C:\Program Files\Command & Conquer Generals Zero Hour",
                @"C:\Program Files (x86)\Command & Conquer Generals Zero Hour",
                @"C:\Games\Specter",
                @"C:\Games\Command & Conquer Generals Zero Hour",
                @"D:\Games\Specter",
                @"D:\Games\Command & Conquer Generals Zero Hour",
                @"E:\Games\Specter"
            };
            foreach (string b in bases)
            {
                if (IsGameRoot(b)) return b;
                // Specter often sits as a subfolder
                try
                {
                    if (Directory.Exists(b))
                    {
                        foreach (string sub in Directory.GetDirectories(b))
                        {
                            if (IsGameRoot(sub)) return sub;
                        }
                    }
                }
                catch { }
            }

            // 5) Scan Program Files shallow for generals.exe next to _SPEC_DATA_ONE.big
            foreach (string root in new[] {
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
                @"C:\", @"D:\", @"E:\"
            })
            {
                if (string.IsNullOrEmpty(root) || !Directory.Exists(root)) continue;
                string hit = ShallowFindGameRoot(root, 2);
                if (hit != null) return hit;
            }

            return null;
        }

        static string ShallowFindGameRoot(string root, int depth)
        {
            try
            {
                if (IsGameRoot(root) && File.Exists(Path.Combine(root, DataBig)))
                    return root;
                if (depth <= 0) return null;
                foreach (string dir in Directory.GetDirectories(root))
                {
                    string name = Path.GetFileName(dir);
                    if (name == null) continue;
                    string lower = name.ToLowerInvariant();
                    if (lower == "windows" || lower == "programdata" || lower.StartsWith("$")) continue;
                    if (IsGameRoot(dir))
                    {
                        // Prefer directories that already have Specter BIGs
                        if (File.Exists(Path.Combine(dir, DataBig)) || lower.Contains("specter") || lower.Contains("generals"))
                            return dir;
                    }
                    if (depth > 1 && (lower.Contains("game") || lower.Contains("ea") || lower.Contains("specter") || lower.Contains("generals") || lower.Contains("command")))
                    {
                        string nested = ShallowFindGameRoot(dir, depth - 1);
                        if (nested != null) return nested;
                    }
                }
            }
            catch { }
            return null;
        }

        static string AskGameRoot(string srcDir)
        {
            Console.WriteLine("Automatic detection failed — please select your Specter GameRoot.");
            using (var dlg = new FolderBrowserDialog())
            {
                dlg.Description = "Select Specter GameRoot (folder containing generals.exe and _SPEC_*.big)";
                dlg.ShowNewFolderButton = false;
                if (Directory.Exists(srcDir)) dlg.SelectedPath = srcDir;
                if (dlg.ShowDialog() == DialogResult.OK)
                {
                    string chosen = dlg.SelectedPath;
                    if (IsGameRoot(chosen)) return chosen;
                    MessageBox.Show(
                        "That folder does not look like a Specter GameRoot.\nIt must contain generals.exe.",
                        AppName, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }

            // Console fallback
            Console.Write("GameRoot path: ");
            try
            {
                string typed = Console.ReadLine();
                if (!string.IsNullOrWhiteSpace(typed))
                {
                    typed = typed.Trim().Trim('"');
                    if (IsGameRoot(typed)) return typed;
                }
            }
            catch { }
            return null;
        }

        static void CreateShortcut(string shortcutPath, string targetPath, string workingDir, string description)
        {
            // Temp PowerShell script avoids fragile command-line quoting with spaces/unicode paths
            string ps1 = Path.Combine(Path.GetTempPath(), "SpecterUltimateShortcut_" + Guid.NewGuid().ToString("N") + ".ps1");
            string script =
                "$ErrorActionPreference = 'Stop'\r\n" +
                "$ws = New-Object -ComObject WScript.Shell\r\n" +
                "$s = $ws.CreateShortcut('" + EscapePs(shortcutPath) + "')\r\n" +
                "$s.TargetPath = '" + EscapePs(targetPath) + "'\r\n" +
                "$s.WorkingDirectory = '" + EscapePs(workingDir) + "'\r\n" +
                "$s.Description = '" + EscapePs(description) + "'\r\n" +
                "$s.Save()\r\n";
            File.WriteAllText(ps1, script, Encoding.UTF8);
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = "-NoProfile -ExecutionPolicy Bypass -File \"" + ps1 + "\"",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };
                using (var p = Process.Start(psi))
                {
                    if (p == null) throw new Exception("Could not start PowerShell to create shortcut.");
                    string err = p.StandardError.ReadToEnd();
                    p.WaitForExit(30000);
                    if (p.ExitCode != 0)
                        throw new Exception("Shortcut creation failed: " + err);
                }
            }
            finally
            {
                try { File.Delete(ps1); } catch { }
            }

            if (!File.Exists(shortcutPath))
                throw new Exception("Desktop shortcut was not created.");
        }

        static string EscapePs(string s)
        {
            if (s == null) return "";
            return s.Replace("'", "''");
        }
    }
}
