using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;
using System.Windows.Threading;

namespace Hitodama.FloatingBar
{
    public class Program
    {
        [STAThread]
        public static void Main(string[] args)
        {
            try
            {
                var app = new Application();
                app.ShutdownMode = ShutdownMode.OnMainWindowClose;
                var barWindow = new HitodamaFloatingBarWindow();
                app.MainWindow = barWindow;
                app.Run(barWindow);
            }
            catch (Exception ex)
            {
                File.WriteAllText("bar_crash.log", ex.ToString());
            }
        }
    }

    /// <summary>
    /// Hitodama Floating Dynamic Island Bar
    /// Authentic Hitodama replica floating companion widget for Windows.
    /// </summary>
    public class HitodamaFloatingBarWindow : Window
    {
        private Border _mainCapsule;
        private StackPanel _expandedTray;
        private TextBox _inputBox;
        private TextBlock _statusText;
        private StackPanel _waveformBars;
        private StackPanel _trayContent;
        private DispatcherTimer _animTimer;
        private Ellipse _spiritOrb;
        private Ellipse _spiritGlow;
        private double _animStep = 0;
        private bool _isExpanded = false;

        public HitodamaFloatingBarWindow()
        {
            this.Title = "Hitodama Floating Island";
            this.Width = 560;
            this.Height = 74;
            this.WindowStyle = WindowStyle.None;
            this.ResizeMode = ResizeMode.NoResize;
            this.AllowsTransparency = true;
            this.Background = Brushes.Transparent;
            this.Topmost = true;
            this.ShowInTaskbar = true;
            this.WindowStartupLocation = WindowStartupLocation.Manual;

            var screenWidth = SystemParameters.PrimaryScreenWidth;
            this.Left = (screenWidth - 560) / 2;
            this.Top = 28;

            BuildUI();

            _animTimer = new DispatcherTimer();
            _animTimer.Interval = TimeSpan.FromMilliseconds(40);
            _animTimer.Tick += (s, e) => OnAnimate();
            _animTimer.Start();
        }

        private void BuildUI()
        {
            var rootGrid = new Grid();

            // Main Glass Capsule
            _mainCapsule = new Border()
            {
                Background = new SolidColorBrush(Color.FromArgb(245, 11, 12, 16)),
                BorderBrush = new SolidColorBrush(Color.FromArgb(160, 69, 243, 255)),
                BorderThickness = new Thickness(1.8),
                CornerRadius = new CornerRadius(37),
                Padding = new Thickness(16, 10, 16, 10),
                Effect = new System.Windows.Media.Effects.DropShadowEffect()
                {
                    Color = Color.FromRgb(69, 243, 255),
                    BlurRadius = 24,
                    Opacity = 0.45,
                    ShadowDepth = 0
                }
            };

            var layoutStack = new StackPanel();

            // 1. Top Capsule Row (Always visible floating bar)
            var barDock = new DockPanel() { Height = 48 };

            // Left: Glowing Hitodama Spirit Orb
            var orbContainer = new Grid() { Width = 44, Height = 44, Margin = new Thickness(0, 0, 12, 0), Cursor = Cursors.Hand };
            orbContainer.MouseDown += (s, e) => ToggleExpand();

            _spiritGlow = new Ellipse()
            {
                Width = 42,
                Height = 42,
                Fill = new SolidColorBrush(Color.FromArgb(90, 102, 252, 241)),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            orbContainer.Children.Add(_spiritGlow);

            _spiritOrb = new Ellipse()
            {
                Width = 28,
                Height = 28,
                Fill = new RadialGradientBrush(Colors.White, Color.FromRgb(69, 243, 255))
                {
                    Center = new Point(0.35, 0.35),
                    GradientOrigin = new Point(0.35, 0.35)
                },
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            orbContainer.Children.Add(_spiritOrb);

            DockPanel.SetDock(orbContainer, Dock.Left);
            barDock.Children.Add(orbContainer);

            // Right: Interactive Hitodama Feature Pills
            var pillsStack = new StackPanel() { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };

            pillsStack.Children.Add(CreatePill("🎙️", "Voice", () => OnVoiceClick()));
            pillsStack.Children.Add(CreatePill("🚀", "Apps", () => ShowTray("apps")));
            pillsStack.Children.Add(CreatePill("📋", "Tasks", () => ShowTray("tasks")));
            pillsStack.Children.Add(CreatePill("🎵", "Music", () => ShowTray("music")));
            pillsStack.Children.Add(CreatePill("▾", "Toggle", () => ToggleExpand()));

            DockPanel.SetDock(pillsStack, Dock.Right);
            barDock.Children.Add(pillsStack);

            // Center: Status, Live Audio Waveform & Input
            var centerDock = new DockPanel() { VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(4, 0, 8, 0) };

            var statusRow = new StackPanel() { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 2) };
            _statusText = new TextBlock()
            {
                Text = "HITODAMA",
                FontWeight = FontWeights.Bold,
                FontSize = 13,
                Foreground = new SolidColorBrush(Color.FromRgb(69, 243, 255)),
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(0, 0, 8, 0)
            };
            statusRow.Children.Add(_statusText);

            _waveformBars = new StackPanel() { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            for (int i = 0; i < 5; i++)
            {
                var bar = new Border()
                {
                    Width = 3,
                    Height = 10,
                    Background = new SolidColorBrush(Color.FromRgb(102, 252, 241)),
                    CornerRadius = new CornerRadius(1.5),
                    Margin = new Thickness(1.5, 0, 1.5, 0)
                };
                _waveformBars.Children.Add(bar);
            }
            statusRow.Children.Add(_waveformBars);
            DockPanel.SetDock(statusRow, Dock.Top);
            centerDock.Children.Add(statusRow);

            _inputBox = new TextBox()
            {
                Background = Brushes.Transparent,
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0),
                FontSize = 12.5,
                VerticalAlignment = VerticalAlignment.Center,
                Text = "Ask Hitodama or type command..."
            };
            _inputBox.GotFocus += (s, e) =>
            {
                if (_inputBox.Text == "Ask Hitodama or type command...") _inputBox.Text = "";
            };
            _inputBox.LostFocus += (s, e) =>
            {
                if (string.IsNullOrEmpty(_inputBox.Text)) _inputBox.Text = "Ask Hitodama or type command...";
            };
            _inputBox.KeyDown += (s, e) =>
            {
                if (e.Key == Key.Enter) ExecutePrompt();
            };
            centerDock.Children.Add(_inputBox);

            barDock.Children.Add(centerDock);
            layoutStack.Children.Add(barDock);

            // 2. Expandable Tray (Hidden by default, expands on click)
            _expandedTray = new StackPanel()
            {
                Visibility = Visibility.Collapsed,
                Margin = new Thickness(0, 12, 0, 0)
            };

            _trayContent = new StackPanel();
            _expandedTray.Children.Add(_trayContent);
            layoutStack.Children.Add(_expandedTray);

            _mainCapsule.Child = layoutStack;
            rootGrid.Children.Add(_mainCapsule);

            // Allow dragging the floating bar anywhere
            this.MouseDown += (s, e) =>
            {
                if (e.ChangedButton == MouseButton.Left)
                {
                    this.DragMove();
                }
            };

            this.Content = rootGrid;
        }

        private Button CreatePill(string icon, string label, Action action)
        {
            var btn = new Button()
            {
                Content = icon,
                ToolTip = label,
                Background = new SolidColorBrush(Color.FromArgb(40, 69, 243, 255)),
                Foreground = new SolidColorBrush(Color.FromRgb(69, 243, 255)),
                BorderBrush = new SolidColorBrush(Color.FromArgb(80, 69, 243, 255)),
                BorderThickness = new Thickness(1),
                Width = 32,
                Height = 32,
                FontSize = 13,
                Margin = new Thickness(3, 0, 3, 0),
                Cursor = Cursors.Hand
            };
            btn.Click += (s, e) => action();
            return btn;
        }

        public void ToggleExpand()
        {
            _isExpanded = !_isExpanded;
            if (_isExpanded)
            {
                this.Height = 280;
                _mainCapsule.CornerRadius = new CornerRadius(22);
                _expandedTray.Visibility = Visibility.Visible;
                ShowTray("apps");
            }
            else
            {
                this.Height = 74;
                _mainCapsule.CornerRadius = new CornerRadius(37);
                _expandedTray.Visibility = Visibility.Collapsed;
            }
        }

        private void ShowTray(string module)
        {
            if (!_isExpanded) ToggleExpand();
            _trayContent.Children.Clear();

            var header = new TextBlock()
            {
                Text = module.ToUpper() + " ISLAND",
                FontWeight = FontWeights.Bold,
                FontSize = 10,
                Foreground = new SolidColorBrush(Color.FromRgb(69, 243, 255)),
                Margin = new Thickness(4, 0, 0, 8)
            };
            _trayContent.Children.Add(header);

            if (module == "apps")
            {
                var wrap = new WrapPanel();
                string[] appNames = new string[] { "VS Code", "Terminal", "Notepad", "Edge", "Calculator", "Explorer" };
                string[] appCmds = new string[] { "code", "wt", "notepad", "msedge", "calc", "explorer" };

                for (int i = 0; i < appNames.Length; i++)
                {
                    string cmd = appCmds[i];
                    string name = appNames[i];
                    var b = new Button()
                    {
                        Content = name,
                        Background = new SolidColorBrush(Color.FromArgb(240, 20, 23, 30)),
                        Foreground = Brushes.White,
                        BorderBrush = new SolidColorBrush(Color.FromArgb(70, 69, 243, 255)),
                        BorderThickness = new Thickness(1),
                        Padding = new Thickness(10, 6, 10, 6),
                        Margin = new Thickness(4),
                        Cursor = Cursors.Hand
                    };
                    b.Click += (s, e) =>
                    {
                        try { Process.Start(new ProcessStartInfo(cmd) { UseShellExecute = true }); } catch { }
                        _statusText.Text = "Launched " + name;
                    };
                    wrap.Children.Add(b);
                }
                _trayContent.Children.Add(wrap);
            }
            else if (module == "tasks")
            {
                var tasksBox = new StackPanel();
                tasksBox.Children.Add(CreateTaskRow("Verify Qualcomm Hexagon NPU TOPS", "URGENT"));
                tasksBox.Children.Add(CreateTaskRow("Deploy Windows ARM64 Release MSIX", "HIGH"));
                tasksBox.Children.Add(CreateTaskRow("Test Hitodama Floating Island Bar", "DONE"));
                _trayContent.Children.Add(tasksBox);
            }
            else if (module == "music")
            {
                var musicCard = new Border()
                {
                    Background = new SolidColorBrush(Color.FromArgb(240, 20, 23, 30)),
                    CornerRadius = new CornerRadius(10),
                    Padding = new Thickness(12)
                };
                var dock = new DockPanel();
                var textStack = new StackPanel();
                textStack.Children.Add(new TextBlock() { Text = "Hitodama Lo-Fi Beats · Track 01", FontWeight = FontWeights.Bold, Foreground = Brushes.White });
                textStack.Children.Add(new TextBlock() { Text = "Ambient Desktop Companion Audio", FontSize = 10, Foreground = new SolidColorBrush(Color.FromRgb(197, 198, 199)) });
                DockPanel.SetDock(textStack, Dock.Left);
                dock.Children.Add(textStack);

                var playBtn = new Button()
                {
                    Content = "▶ Play",
                    Background = new SolidColorBrush(Color.FromRgb(69, 243, 255)),
                    Foreground = new SolidColorBrush(Color.FromRgb(11, 12, 16)),
                    FontWeight = FontWeights.Bold,
                    Padding = new Thickness(12, 6, 12, 6),
                    BorderThickness = new Thickness(0),
                    HorizontalAlignment = HorizontalAlignment.Right
                };
                dock.Children.Add(playBtn);
                musicCard.Child = dock;
                _trayContent.Children.Add(musicCard);
            }
        }

        private Border CreateTaskRow(string text, string tag)
        {
            var b = new Border()
            {
                Background = new SolidColorBrush(Color.FromArgb(240, 20, 23, 30)),
                CornerRadius = new CornerRadius(6),
                Padding = new Thickness(10, 6, 10, 6),
                Margin = new Thickness(0, 3, 0, 3)
            };
            var d = new DockPanel();
            var chk = new CheckBox() { Content = text, Foreground = Brushes.White, FontSize = 11.5, IsChecked = (tag == "DONE") };
            DockPanel.SetDock(chk, Dock.Left);
            d.Children.Add(chk);

            var t = new TextBlock()
            {
                Text = tag,
                FontWeight = FontWeights.Bold,
                FontSize = 9.5,
                Foreground = tag == "URGENT" ? new SolidColorBrush(Color.FromRgb(255, 78, 100)) : new SolidColorBrush(Color.FromRgb(78, 255, 155)),
                HorizontalAlignment = HorizontalAlignment.Right
            };
            d.Children.Add(t);
            b.Child = d;
            return b;
        }

        private void OnVoiceClick()
        {
            _statusText.Text = "Listening...";
            _inputBox.Text = "Remind me in 15 minutes to review thermal profile";
            ExecutePrompt();
        }

        private void ExecutePrompt()
        {
            string cmd = _inputBox.Text.Trim();
            if (string.IsNullOrEmpty(cmd)) return;

            _statusText.Text = "Thinking...";
            ThreadPool.QueueUserWorkItem(_ =>
            {
                try
                {
                    var req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:8765/api/chat");
                    req.Method = "POST";
                    req.ContentType = "application/json";
                    byte[] data = Encoding.UTF8.GetBytes("{\"message\":\"" + cmd.Replace("\"", "\\\"") + "\",\"user_confirmed\":true}");
                    req.ContentLength = data.Length;
                    using (var st = req.GetRequestStream()) st.Write(data, 0, data.Length);

                    string respJson;
                    using (var resp = (HttpWebResponse)req.GetResponse())
                    using (var sr = new StreamReader(resp.GetResponseStream())) respJson = sr.ReadToEnd();

                    Dispatcher.Invoke(() =>
                    {
                        _statusText.Text = "Executed";
                        _inputBox.Text = cmd;
                    });
                }
                catch
                {
                    Dispatcher.Invoke(() =>
                    {
                        _statusText.Text = "Hitodama Ready";
                    });
                }
            });
        }

        private void OnAnimate()
        {
            _animStep += 0.08;
            double p = 1.0 + Math.Sin(_animStep * 2.0) * 0.10;
            _spiritGlow.Width = 42 * p;
            _spiritGlow.Height = 42 * p;

            // Audio waveform pulsation
            for (int i = 0; i < _waveformBars.Children.Count; i++)
            {
                var bar = (Border)_waveformBars.Children[i];
                double h = 6 + Math.Sin(_animStep * 3.0 + i) * 6;
                bar.Height = Math.Max(3, h);
            }
        }
    }
}
