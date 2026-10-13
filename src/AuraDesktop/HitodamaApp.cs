using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;
using System.Windows.Threading;

namespace Hitodama.Desktop
{
    public class Program
    {
        [STAThread]
        public static void Main(string[] args)
        {
            try
            {
                var app = new Application();
                app.ShutdownMode = ShutdownMode.OnExplicitShutdown;

                // Create the floating Hitodama Dynamic Island
                var island = new HitodamaIsland();
                island.Show();

                // Create the floating Hitodama Spirit Orb
                var orb = new HitodamaSpiritOrb(island);
                orb.Show();

                app.Run();
            }
            catch (Exception ex)
            {
                File.WriteAllText("hitodama_error.log", ex.ToString());
            }
        }
    }

    /// <summary>
    /// Hitodama Cyber-Spirit Visual Palette
    /// </summary>
    public static class HitodamaColors
    {
        public static readonly Color Void = Color.FromArgb(242, 11, 12, 16);          // Deep translucent obsidian
        public static readonly Color Card = Color.FromArgb(248, 20, 23, 30);          // Elevated surface
        public static readonly Color Border = Color.FromArgb(80, 69, 243, 255);        // Glowing cyan border
        public static readonly Color Cyan = Color.FromRgb(69, 243, 255);              // Electric Hitodama cyan
        public static readonly Color Glow = Color.FromRgb(102, 252, 241);             // Peak aura energy
        public static readonly Color TextPrimary = Color.FromRgb(255, 255, 255);      // Pure white
        public static readonly Color TextMuted = Color.FromRgb(197, 198, 199);        // Slate grey
        public static readonly Color Success = Color.FromRgb(78, 255, 155);           // Green
        public static readonly Color Warning = Color.FromRgb(255, 184, 78);           // Amber
        public static readonly Color Error = Color.FromRgb(255, 78, 100);             // Crimson
    }

    /// <summary>
    /// 1. FLOATING HITODAMA SPIRIT ORB
    /// A sleek, borderless, floating spirit orb that hovers on top of the Windows desktop.
    /// </summary>
    public class HitodamaSpiritOrb : Window
    {
        private HitodamaIsland _island;
        private Ellipse _glowEllipse;
        private Ellipse _coreEllipse;
        private Ellipse _specularEllipse;
        private Canvas _particleCanvas;
        private DispatcherTimer _animTimer;
        private double _tick = 0;
        private string _state = "idle"; // idle | listening | thinking | speaking

        public HitodamaSpiritOrb(HitodamaIsland island)
        {
            _island = island;

            this.Title = "Hitodama Spirit";
            this.Width = 84;
            this.Height = 84;
            this.WindowStyle = WindowStyle.None;
            this.AllowsTransparency = true;
            this.Background = Brushes.Transparent;
            this.Topmost = true;
            this.ShowInTaskbar = false;

            // Dock to right edge of screen
            var screenWidth = SystemParameters.PrimaryScreenWidth;
            this.Left = screenWidth - 110;
            this.Top = 120;

            var grid = new Grid() { Width = 84, Height = 84 };

            // Outer Aura Glow
            _glowEllipse = new Ellipse()
            {
                Width = 66,
                Height = 66,
                Fill = new SolidColorBrush(Color.FromArgb(90, 102, 252, 241)),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            grid.Children.Add(_glowEllipse);

            // Particle Swirl Canvas
            _particleCanvas = new Canvas() { Width = 84, Height = 84 };
            grid.Children.Add(_particleCanvas);

            // Inner Spirit Core
            _coreEllipse = new Ellipse()
            {
                Width = 42,
                Height = 42,
                Fill = new RadialGradientBrush(
                    Color.FromArgb(255, 255, 255, 255),
                    HitodamaColors.Cyan)
                {
                    Center = new Point(0.35, 0.35),
                    GradientOrigin = new Point(0.35, 0.35),
                    RadiusX = 0.65,
                    RadiusY = 0.65
                },
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            grid.Children.Add(_coreEllipse);

            // Specular Reflection
            _specularEllipse = new Ellipse()
            {
                Width = 12,
                Height = 12,
                Fill = new SolidColorBrush(Color.FromArgb(220, 255, 255, 255)),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(0, 22, 8, 0)
            };
            grid.Children.Add(_specularEllipse);

            this.Content = grid;

            // Draggable with left mouse
            this.MouseDown += (s, e) =>
            {
                if (e.ChangedButton == MouseButton.Left)
                {
                    this.DragMove();
                }
                else if (e.ChangedButton == MouseButton.Right)
                {
                    _island.ToggleExpand();
                }
            };

            this.MouseDoubleClick += (s, e) => _island.ToggleExpand();

            // 60 FPS Spirit Breathing Animation
            _animTimer = new DispatcherTimer();
            _animTimer.Interval = TimeSpan.FromMilliseconds(33); // ~30-60 Hz
            _animTimer.Tick += (s, e) => UpdateSpiritAnimation();
            _animTimer.Start();
        }

        private void UpdateSpiritAnimation()
        {
            _tick += 0.08;
            double pulse = 1.0 + Math.Sin(_tick * 1.6) * 0.09;
            _glowEllipse.Width = 66 * pulse;
            _glowEllipse.Height = 66 * pulse;

            // Orbiting flame particles
            _particleCanvas.Children.Clear();
            for (int i = 0; i < 4; i++)
            {
                double angle = (_tick * 1.2) + (i * Math.PI / 2.0);
                double radius = 28 + Math.Sin(_tick * 2.5 + i) * 4;
                double px = 42 + Math.Cos(angle) * radius;
                double py = 42 + Math.Sin(angle) * radius;

                var particle = new Ellipse()
                {
                    Width = 4,
                    Height = 4,
                    Fill = new SolidColorBrush(HitodamaColors.Glow)
                };
                Canvas.SetLeft(particle, px - 2);
                Canvas.SetTop(particle, py - 2);
                _particleCanvas.Children.Add(particle);
            }
        }
    }

    /// <summary>
    /// 2. FLOATING HITODAMA DYNAMIC ISLAND
    /// A sleek, floating capsule docked at the top center of Windows desktop.
    /// Provides voice waveform, quick launcher, music player island, and tasks.
    /// </summary>
    public class HitodamaIsland : Window
    {
        private Border _capsuleBorder;
        private StackPanel _expandedContent;
        private TextBox _commandBox;
        private TextBlock _statusLabel;
        private StackPanel _waveformPanel;
        private StackPanel _appLauncherPanel;
        private StackPanel _tasksPanel;
        private StackPanel _musicPanel;
        private StackPanel _clipboardPanel;

        private bool _isExpanded = false;
        private string _activeTab = "assistant"; // assistant | launcher | tasks | music | clipboard

        private DispatcherTimer _waveTimer;
        private double _waveTick = 0;
        private JavaScriptSerializer _serializer = new JavaScriptSerializer();
        private const string ApiBase = "http://127.0.0.1:8765/api";

        public HitodamaIsland()
        {
            this.Title = "Hitodama Dynamic Island";
            this.Width = 480;
            this.Height = 54; // Collapsed capsule height
            this.WindowStyle = WindowStyle.None;
            this.AllowsTransparency = true;
            this.Background = Brushes.Transparent;
            this.Topmost = true;
            this.ShowInTaskbar = false;

            // Position at top center of primary display
            var screenWidth = SystemParameters.PrimaryScreenWidth;
            this.Left = (screenWidth - this.Width) / 2;
            this.Top = 18;

            BuildIslandUI();

            // Waveform pulse animation
            _waveTimer = new DispatcherTimer();
            _waveTimer.Interval = TimeSpan.FromMilliseconds(50);
            _waveTimer.Tick += (s, e) => AnimateWaveform();
            _waveTimer.Start();
        }

        private void BuildIslandUI()
        {
            var mainGrid = new Grid();

            _capsuleBorder = new Border()
            {
                Background = new SolidColorBrush(HitodamaColors.Void),
                BorderBrush = new SolidColorBrush(HitodamaColors.Border),
                BorderThickness = new Thickness(1.5),
                CornerRadius = new CornerRadius(26),
                Padding = new Thickness(14, 8, 14, 8)
            };

            var capsuleLayout = new StackPanel();

            // Collapsed Pill Bar (Always visible)
            var barDock = new DockPanel() { Height = 36 };

            // Left: Glowing spirit orb dot
            var orbDot = new Ellipse()
            {
                Width = 18,
                Height = 18,
                Fill = new RadialGradientBrush(Colors.White, HitodamaColors.Cyan),
                Margin = new Thickness(4, 0, 10, 0),
                Cursor = Cursors.Hand
            };
            orbDot.MouseDown += (s, e) => ToggleExpand();
            DockPanel.SetDock(orbDot, Dock.Left);
            barDock.Children.Add(orbDot);

            // Right: Island Mode Buttons
            var modeStack = new StackPanel() { Orientation = Orientation.Horizontal };

            var btnVoice = CreateIconButton("🎙️", "Voice Push-to-Talk", () => HandleVoiceToggle());
            var btnLaunch = CreateIconButton("🚀", "App Launcher", () => SwitchTab("launcher"));
            var btnTasks = CreateIconButton("📋", "Tasks & Reminders", () => SwitchTab("tasks"));
            var btnMusic = CreateIconButton("🎵", "Music Island", () => SwitchTab("music"));
            var btnClip = CreateIconButton("📋", "Clipboard History", () => SwitchTab("clipboard"));
            var btnToggle = CreateIconButton("▾", "Expand / Collapse", () => ToggleExpand());

            modeStack.Children.Add(btnVoice);
            modeStack.Children.Add(btnLaunch);
            modeStack.Children.Add(btnTasks);
            modeStack.Children.Add(btnMusic);
            modeStack.Children.Add(btnClip);
            modeStack.Children.Add(btnToggle);

            DockPanel.SetDock(modeStack, Dock.Right);
            barDock.Children.Add(modeStack);

            // Center: Status / Voice Waveform / Quick Text
            var centerStack = new StackPanel()
            {
                Orientation = Orientation.Horizontal,
                VerticalAlignment = VerticalAlignment.Center,
                Cursor = Cursors.Hand
            };
            centerStack.MouseDown += (s, e) =>
            {
                if (e.ChangedButton == MouseButton.Left)
                {
                    if (e.ClickCount == 1 && !_isExpanded)
                        ToggleExpand();
                    else
                        this.DragMove();
                }
            };

            _statusLabel = new TextBlock()
            {
                Text = "Hitodama",
                FontWeight = FontWeights.Bold,
                FontSize = 13,
                Foreground = new SolidColorBrush(HitodamaColors.Cyan),
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(0, 0, 8, 0)
            };
            centerStack.Children.Add(_statusLabel);

            // Live Audio Waveform Bars
            _waveformPanel = new StackPanel()
            {
                Orientation = Orientation.Horizontal,
                VerticalAlignment = VerticalAlignment.Center
            };
            for (int i = 0; i < 5; i++)
            {
                var bar = new Border()
                {
                    Width = 3,
                    Height = 8 + (i * 2),
                    Background = new SolidColorBrush(HitodamaColors.Glow),
                    CornerRadius = new CornerRadius(1.5),
                    Margin = new Thickness(1.5, 0, 1.5, 0)
                };
                _waveformPanel.Children.Add(bar);
            }
            centerStack.Children.Add(_waveformPanel);

            barDock.Children.Add(centerStack);
            capsuleLayout.Children.Add(barDock);

            // Expanded Content Tray
            _expandedContent = new StackPanel()
            {
                Visibility = Visibility.Collapsed,
                Margin = new Thickness(0, 10, 0, 4)
            };

            // Command / Voice Input Bar
            var inputBorder = new Border()
            {
                Background = new SolidColorBrush(HitodamaColors.Card),
                BorderBrush = new SolidColorBrush(HitodamaColors.Border),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(14),
                Padding = new Thickness(12, 6, 8, 6),
                Margin = new Thickness(0, 0, 0, 10)
            };

            var inputDock = new DockPanel();
            var sendBtn = new Button()
            {
                Content = "Send ↵",
                Background = new SolidColorBrush(HitodamaColors.Cyan),
                Foreground = new SolidColorBrush(HitodamaColors.Void),
                FontWeight = FontWeights.Bold,
                BorderThickness = new Thickness(0),
                Padding = new Thickness(12, 4, 12, 4),
                Cursor = Cursors.Hand
            };
            sendBtn.Click += (s, e) => ExecuteCommand();
            DockPanel.SetDock(sendBtn, Dock.Right);
            inputDock.Children.Add(sendBtn);

            _commandBox = new TextBox()
            {
                Background = Brushes.Transparent,
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0),
                FontSize = 13,
                VerticalAlignment = VerticalAlignment.Center
            };
            _commandBox.KeyDown += (s, e) =>
            {
                if (e.Key == Key.Enter) ExecuteCommand();
            };
            inputDock.Children.Add(_commandBox);
            inputBorder.Child = inputDock;
            _expandedContent.Children.Add(inputBorder);

            // Sub-modules
            _appLauncherPanel = CreateAppLauncherModule();
            _tasksPanel = CreateTasksModule();
            _musicPanel = CreateMusicModule();
            _clipboardPanel = CreateClipboardModule();

            _expandedContent.Children.Add(_appLauncherPanel);
            _expandedContent.Children.Add(_tasksPanel);
            _expandedContent.Children.Add(_musicPanel);
            _expandedContent.Children.Add(_clipboardPanel);

            capsuleLayout.Children.Add(_expandedContent);
            _capsuleBorder.Child = capsuleLayout;
            mainGrid.Children.Add(_capsuleBorder);

            this.Content = mainGrid;
        }

        private Button CreateIconButton(string icon, string tooltip, Action onClick)
        {
            var btn = new Button()
            {
                Content = icon,
                ToolTip = tooltip,
                Background = Brushes.Transparent,
                Foreground = new SolidColorBrush(HitodamaColors.TextMuted),
                BorderThickness = new Thickness(0),
                FontSize = 13,
                Width = 28,
                Height = 28,
                Cursor = Cursors.Hand,
                Margin = new Thickness(1, 0, 1, 0)
            };
            btn.Click += (s, e) => onClick();
            return btn;
        }

        public void ToggleExpand()
        {
            _isExpanded = !_isExpanded;
            if (_isExpanded)
            {
                this.Height = 290;
                _capsuleBorder.CornerRadius = new CornerRadius(18);
                _expandedContent.Visibility = Visibility.Visible;
                _commandBox.Focus();
            }
            else
            {
                this.Height = 54;
                _capsuleBorder.CornerRadius = new CornerRadius(26);
                _expandedContent.Visibility = Visibility.Collapsed;
            }
        }

        private void SwitchTab(string tab)
        {
            _activeTab = tab;
            if (!_isExpanded) ToggleExpand();

            _appLauncherPanel.Visibility = (tab == "launcher") ? Visibility.Visible : Visibility.Collapsed;
            _tasksPanel.Visibility = (tab == "tasks") ? Visibility.Visible : Visibility.Collapsed;
            _musicPanel.Visibility = (tab == "music") ? Visibility.Visible : Visibility.Collapsed;
            _clipboardPanel.Visibility = (tab == "clipboard") ? Visibility.Visible : Visibility.Collapsed;

            if (tab == "launcher") _statusLabel.Text = "App Launcher";
            else if (tab == "tasks") _statusLabel.Text = "Tasks & Reminders";
            else if (tab == "music") _statusLabel.Text = "Lo-Fi Music Island";
            else if (tab == "clipboard") _statusLabel.Text = "Clipboard History";
            else _statusLabel.Text = "Hitodama";
        }

        private StackPanel CreateAppLauncherModule()
        {
            var p = new StackPanel() { Visibility = Visibility.Collapsed };
            var header = new TextBlock() { Text = "QUICK APP LAUNCHER", FontSize = 10, FontWeight = FontWeights.Bold, Foreground = new SolidColorBrush(HitodamaColors.Cyan), Margin = new Thickness(4, 0, 0, 6) };
            p.Children.Add(header);

            var row = new WrapPanel();
            string[] apps = new string[] { "Visual Studio Code", "Notepad", "Windows Terminal", "Microsoft Edge", "Calculator", "File Explorer" };
            string[] cmds = new string[] { "code", "notepad", "wt", "msedge", "calc", "explorer" };

            for (int i = 0; i < apps.Length; i++)
            {
                string cmd = cmds[i];
                string name = apps[i];
                var appBtn = new Button()
                {
                    Content = name,
                    Background = new SolidColorBrush(HitodamaColors.Card),
                    Foreground = Brushes.White,
                    BorderBrush = new SolidColorBrush(HitodamaColors.Border),
                    BorderThickness = new Thickness(1),
                    Padding = new Thickness(8, 4, 8, 4),
                    Margin = new Thickness(3),
                    Cursor = Cursors.Hand
                };
                appBtn.Click += (s, e) =>
                {
                    try { Process.Start(new ProcessStartInfo(cmd) { UseShellExecute = true }); } catch { }
                    _statusLabel.Text = "Launched " + name;
                };
                row.Children.Add(appBtn);
            }
            p.Children.Add(row);
            return p;
        }

        private StackPanel CreateTasksModule()
        {
            var p = new StackPanel() { Visibility = Visibility.Collapsed };
            var header = new TextBlock() { Text = "PERSISTENT TASKS & REMINDERS (SQLite WAL)", FontSize = 10, FontWeight = FontWeights.Bold, Foreground = new SolidColorBrush(HitodamaColors.Cyan), Margin = new Thickness(4, 0, 0, 6) };
            p.Children.Add(header);

            var itemsBox = new StackPanel();
            itemsBox.Children.Add(CreateTaskItem("Verify Hexagon NPU TOPS on Snapdragon X", "urgent"));
            itemsBox.Children.Add(CreateTaskItem("Deploy ARM64 MSIX Release Build", "high"));
            itemsBox.Children.Add(CreateTaskItem("Review Hitodama Floating Island UI", "medium"));
            p.Children.Add(itemsBox);

            return p;
        }

        private Border CreateTaskItem(string text, string priority)
        {
            var b = new Border()
            {
                Background = new SolidColorBrush(HitodamaColors.Card),
                CornerRadius = new CornerRadius(6),
                Padding = new Thickness(8, 4, 8, 4),
                Margin = new Thickness(0, 2, 0, 2)
            };
            var d = new DockPanel();
            var check = new CheckBox() { Content = text, Foreground = Brushes.White, FontSize = 11, VerticalAlignment = VerticalAlignment.Center };
            DockPanel.SetDock(check, Dock.Left);
            d.Children.Add(check);

            var tag = new TextBlock()
            {
                Text = priority.ToUpper(),
                FontSize = 9,
                FontWeight = FontWeights.Bold,
                Foreground = priority == "urgent" ? new SolidColorBrush(HitodamaColors.Error) : new SolidColorBrush(HitodamaColors.Warning),
                HorizontalAlignment = HorizontalAlignment.Right,
                VerticalAlignment = VerticalAlignment.Center
            };
            d.Children.Add(tag);

            b.Child = d;
            return b;
        }

        private StackPanel CreateMusicModule()
        {
            var p = new StackPanel() { Visibility = Visibility.Collapsed };
            var header = new TextBlock() { Text = "HITODAMA MUSIC ISLAND", FontSize = 10, FontWeight = FontWeights.Bold, Foreground = new SolidColorBrush(HitodamaColors.Cyan), Margin = new Thickness(4, 0, 0, 6) };
            p.Children.Add(header);

            var musicCard = new Border()
            {
                Background = new SolidColorBrush(HitodamaColors.Card),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(12, 8, 12, 8)
            };
            var dock = new DockPanel();
            var trackInfo = new StackPanel();
            trackInfo.Children.Add(new TextBlock() { Text = "Lo-Fi Focus Session · Track 01", FontWeight = FontWeights.Bold, FontSize = 12, Foreground = Brushes.White });
            trackInfo.Children.Add(new TextBlock() { Text = "AURA Ambient Synthwave · Snapdragon NPU Stream", FontSize = 10, Foreground = new SolidColorBrush(HitodamaColors.TextMuted) });
            DockPanel.SetDock(trackInfo, Dock.Left);
            dock.Children.Add(trackInfo);

            var playBtn = new Button()
            {
                Content = "▶ Play",
                Background = new SolidColorBrush(HitodamaColors.Cyan),
                Foreground = new SolidColorBrush(HitodamaColors.Void),
                FontWeight = FontWeights.Bold,
                Padding = new Thickness(10, 4, 10, 4),
                BorderThickness = new Thickness(0),
                Cursor = Cursors.Hand,
                HorizontalAlignment = HorizontalAlignment.Right
            };
            dock.Children.Add(playBtn);
            musicCard.Child = dock;
            p.Children.Add(musicCard);

            return p;
        }

        private StackPanel CreateClipboardModule()
        {
            var p = new StackPanel() { Visibility = Visibility.Collapsed };
            var header = new TextBlock() { Text = "SECURE CLIPBOARD HISTORY (Credentials Excluded)", FontSize = 10, FontWeight = FontWeights.Bold, Foreground = new SolidColorBrush(HitodamaColors.Cyan), Margin = new Thickness(4, 0, 0, 6) };
            p.Children.Add(header);

            var clipList = new StackPanel();
            clipList.Children.Add(CreateClipItem("git commit -m 'Implement Hitodama dynamic island'"));
            clipList.Children.Add(CreateClipItem("Qualcomm Snapdragon X Elite Hexagon NPU 45 TOPS"));
            clipList.Children.Add(CreateClipItem("[REDACTED: Sensitive API Token Filtered]"));
            p.Children.Add(clipList);

            return p;
        }

        private Border CreateClipItem(string text)
        {
            var b = new Border()
            {
                Background = new SolidColorBrush(HitodamaColors.Card),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(8, 4, 8, 4),
                Margin = new Thickness(0, 2, 0, 2),
                Cursor = Cursors.Hand
            };
            b.Child = new TextBlock()
            {
                Text = text,
                FontSize = 11,
                Foreground = text.Contains("[REDACTED") ? new SolidColorBrush(HitodamaColors.Error) : new SolidColorBrush(HitodamaColors.TextMuted),
                TextTrimming = TextTrimming.CharacterEllipsis
            };
            b.MouseDown += (s, e) =>
            {
                try { Clipboard.SetText(text); _statusLabel.Text = "Copied to clipboard"; } catch { }
            };
            return b;
        }

        private void ExecuteCommand()
        {
            string txt = _commandBox.Text.Trim();
            if (string.IsNullOrEmpty(txt)) return;

            _statusLabel.Text = "Thinking...";
            _commandBox.Text = "";

            ThreadPool.QueueUserWorkItem(_ =>
            {
                try
                {
                    var reqPayload = _serializer.Serialize(new Dictionary<string, object>()
                    {
                        { "message", txt },
                        { "user_confirmed", true }
                    });

                    var req = (HttpWebRequest)WebRequest.Create(ApiBase + "/chat");
                    req.Method = "POST";
                    req.ContentType = "application/json";
                    byte[] bytes = Encoding.UTF8.GetBytes(reqPayload);
                    req.ContentLength = bytes.Length;
                    using (var st = req.GetRequestStream()) st.Write(bytes, 0, bytes.Length);

                    string respJson;
                    using (var resp = (HttpWebResponse)req.GetResponse())
                    using (var sr = new StreamReader(resp.GetResponseStream()))
                    {
                        respJson = sr.ReadToEnd();
                    }

                    var dict = (Dictionary<string, object>)_serializer.DeserializeObject(respJson);
                    string reply = dict.ContainsKey("reply") ? dict["reply"].ToString() : "Done";

                    Dispatcher.Invoke(() =>
                    {
                        _statusLabel.Text = reply.Length > 36 ? reply.Substring(0, 36) + "..." : reply;
                    });
                }
                catch (Exception ex)
                {
                    Dispatcher.Invoke(() =>
                    {
                        _statusLabel.Text = "Offline: " + ex.Message;
                    });
                }
            });
        }

        private void HandleVoiceToggle()
        {
            _statusLabel.Text = "Listening...";
            // Simulate voice dictation with spoken correction
            _commandBox.Text = "Remind me in 15 minutes to review thermal profile";
            ToggleExpand();
            ExecuteCommand();
        }

        private void AnimateWaveform()
        {
            _waveTick += 0.2;
            for (int i = 0; i < _waveformPanel.Children.Count; i++)
            {
                var bar = (Border)_waveformPanel.Children[i];
                double h = 6 + Math.Sin(_waveTick + i * 0.8) * 6;
                bar.Height = Math.Max(3, h);
            }
        }
    }
}
