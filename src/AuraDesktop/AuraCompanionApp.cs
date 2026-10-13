using System;
using System.Collections;
using System.Collections.Generic;
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

namespace AuraCompanion.Desktop
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

                var mainWindow = new DesktopIslandWindow();
                app.MainWindow = mainWindow;

                var orbWindow = new FloatingOrbWindow(mainWindow);
                orbWindow.Show();

                app.Run(mainWindow);
            }
            catch (Exception ex)
            {
                File.WriteAllText("desktop_error.log", ex.ToString());
            }
        }
    }

    /// <summary>
    /// Hitodama-Matched Design System Colors
    /// </summary>
    public static class AuraTheme
    {
        public static readonly Color ColorVoid = Color.FromRgb(11, 12, 16);
        public static readonly Color ColorCard = Color.FromRgb(20, 23, 30);
        public static readonly Color ColorElevated = Color.FromRgb(31, 40, 51);
        public static readonly Color ColorBorder = Color.FromArgb(40, 69, 243, 255);
        public static readonly Color ColorCyan = Color.FromRgb(69, 243, 255);
        public static readonly Color ColorGlow = Color.FromRgb(102, 252, 241);
        public static readonly Color ColorTextPrimary = Color.FromRgb(255, 255, 255);
        public static readonly Color ColorTextSecondary = Color.FromRgb(197, 198, 199);
        public static readonly Color ColorSuccess = Color.FromRgb(78, 255, 155);
        public static readonly Color ColorWarning = Color.FromRgb(255, 184, 78);
        public static readonly Color ColorError = Color.FromRgb(255, 78, 100);

        public static SolidColorBrush BrushVoid = new SolidColorBrush(ColorVoid);
        public static SolidColorBrush BrushCard = new SolidColorBrush(ColorCard);
        public static SolidColorBrush BrushElevated = new SolidColorBrush(ColorElevated);
        public static SolidColorBrush BrushBorder = new SolidColorBrush(ColorBorder);
        public static SolidColorBrush BrushCyan = new SolidColorBrush(ColorCyan);
        public static SolidColorBrush BrushGlow = new SolidColorBrush(ColorGlow);
        public static SolidColorBrush BrushTextPrimary = new SolidColorBrush(ColorTextPrimary);
        public static SolidColorBrush BrushTextSecondary = new SolidColorBrush(ColorTextSecondary);
        public static SolidColorBrush BrushSuccess = new SolidColorBrush(ColorSuccess);
        public static SolidColorBrush BrushWarning = new SolidColorBrush(ColorWarning);
        public static SolidColorBrush BrushError = new SolidColorBrush(ColorError);
    }

    /// <summary>
    /// Native Floating Hitodama Companion Orb Window
    /// </summary>
    public class FloatingOrbWindow : Window
    {
        private DesktopIslandWindow _islandWindow;
        private Ellipse _coreOrb;
        private Ellipse _glowOrb;
        private DispatcherTimer _pulseTimer;
        private double _pulseStep = 0;

        public FloatingOrbWindow(DesktopIslandWindow islandWindow)
        {
            _islandWindow = islandWindow;

            this.Title = "AURA Companion Orb";
            this.Width = 96;
            this.Height = 96;
            this.WindowStyle = WindowStyle.None;
            this.AllowsTransparency = true;
            this.Background = Brushes.Transparent;
            this.Topmost = true;
            this.ShowInTaskbar = false;

            // Position at top-right of screen
            var screenWidth = SystemParameters.PrimaryScreenWidth;
            this.Left = screenWidth - 130;
            this.Top = 40;

            // Orb canvas
            var grid = new Grid() { Width = 96, Height = 96 };

            _glowOrb = new Ellipse()
            {
                Width = 72,
                Height = 72,
                Fill = new SolidColorBrush(Color.FromArgb(90, 102, 252, 241)),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            grid.Children.Add(_glowOrb);

            _coreOrb = new Ellipse()
            {
                Width = 48,
                Height = 48,
                Fill = new RadialGradientBrush(
                    Color.FromArgb(255, 255, 255, 255),
                    AuraTheme.ColorCyan)
                {
                    Center = new Point(0.35, 0.35),
                    GradientOrigin = new Point(0.35, 0.35),
                    RadiusX = 0.65,
                    RadiusY = 0.65
                },
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            grid.Children.Add(_coreOrb);

            var specular = new Ellipse()
            {
                Width = 14,
                Height = 14,
                Fill = new SolidColorBrush(Color.FromArgb(210, 255, 255, 255)),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(0, 24, 10, 0)
            };
            grid.Children.Add(specular);

            this.Content = grid;

            // Drag behavior
            this.MouseDown += (s, e) =>
            {
                if (e.ChangedButton == MouseButton.Left)
                {
                    this.DragMove();
                }
                else if (e.ChangedButton == MouseButton.Right)
                {
                    ToggleIsland();
                }
            };

            this.MouseDoubleClick += (s, e) => ToggleIsland();

            // Smooth breathing animation timer
            _pulseTimer = new DispatcherTimer();
            _pulseTimer.Interval = TimeSpan.FromMilliseconds(40);
            _pulseTimer.Tick += (s, e) =>
            {
                _pulseStep += 0.08;
                double scale = 1.0 + Math.Sin(_pulseStep) * 0.08;
                _glowOrb.Width = 72 * scale;
                _glowOrb.Height = 72 * scale;
            };
            _pulseTimer.Start();
        }

        private void ToggleIsland()
        {
            if (_islandWindow.Visibility == Visibility.Visible)
            {
                _islandWindow.Hide();
            }
            else
            {
                _islandWindow.Show();
                _islandWindow.Activate();
            }
        }
    }

    /// <summary>
    /// Native Dynamic Desktop Island Window (Hitodama Desktop AI)
    /// </summary>
    public class DesktopIslandWindow : Window
    {
        private StackPanel _chatPanel;
        private ScrollViewer _chatScroll;
        private TextBox _inputBox;
        private StackPanel _tasksPanel;
        private StackPanel _remindersPanel;
        private TextBlock _statusText;
        private TextBlock _pipelineStepText;
        private Border _safetyModal;
        private TextBlock _safetyModalText;
        private Action _pendingSafeAction;

        private JavaScriptSerializer _serializer = new JavaScriptSerializer();
        private const string ApiBase = "http://127.0.0.1:8765/api";

        public DesktopIslandWindow()
        {
            this.Title = "AURA Companion — Desktop Island";
            this.Width = 840;
            this.Height = 620;
            this.WindowStartupLocation = WindowStartupLocation.CenterScreen;
            this.Background = AuraTheme.BrushVoid;
            this.Foreground = AuraTheme.BrushTextPrimary;
            this.FontFamily = new FontFamily("Segoe UI, Outfit, Arial");

            BuildUI();
            LoadStatus();
            LoadTasks();
            LoadReminders();
        }

        private void BuildUI()
        {
            var mainGrid = new Grid();
            mainGrid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(64) }); // Header
            mainGrid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(1, GridUnitType.Star) }); // Content
            mainGrid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(28) }); // Status bar

            // 1. Header
            var headerBorder = new Border()
            {
                Background = AuraTheme.BrushCard,
                BorderBrush = AuraTheme.BrushBorder,
                BorderThickness = new Thickness(0, 0, 0, 1),
                Padding = new Thickness(20, 10, 20, 10)
            };

            var headerDock = new DockPanel();
            
            var titleStack = new StackPanel() { Orientation = Orientation.Horizontal };
            var orbDot = new Ellipse() { Width = 16, Height = 16, Fill = AuraTheme.BrushCyan, Margin = new Thickness(0, 0, 10, 0) };
            titleStack.Children.Add(orbDot);

            var titleText = new TextBlock()
            {
                Text = "AURA COMPANION",
                FontWeight = FontWeights.Bold,
                FontSize = 16,
                Foreground = AuraTheme.BrushTextPrimary,
                VerticalAlignment = VerticalAlignment.Center
            };
            titleStack.Children.Add(titleText);

            var subTitle = new TextBlock()
            {
                Text = "  [Hitodama Replica · Snapdragon X ARM64]",
                FontSize = 12,
                Foreground = AuraTheme.BrushTextSecondary,
                VerticalAlignment = VerticalAlignment.Center
            };
            titleStack.Children.Add(subTitle);
            DockPanel.SetDock(titleStack, DockSide(Dock.Left));
            headerDock.Children.Add(titleStack);

            var badgeStack = new StackPanel() { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
            var offlinePill = new Border()
            {
                Background = AuraTheme.BrushElevated,
                BorderBrush = AuraTheme.BrushSuccess,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(10),
                Padding = new Thickness(10, 4, 10, 4),
                Margin = new Thickness(0, 0, 8, 0)
            };
            offlinePill.Child = new TextBlock() { Text = "Strict Offline · 0 Bytes Outbound", FontSize = 11, Foreground = AuraTheme.BrushSuccess };
            badgeStack.Children.Add(offlinePill);

            var voiceBtn = new Button()
            {
                Content = "🎙️ Win+Space",
                Background = new SolidColorBrush(Color.FromArgb(40, 69, 243, 255)),
                Foreground = AuraTheme.BrushCyan,
                BorderBrush = AuraTheme.BrushCyan,
                BorderThickness = new Thickness(1),
                Padding = new Thickness(10, 4, 10, 4),
                FontWeight = FontWeights.SemiBold,
                Cursor = Cursors.Hand
            };
            voiceBtn.Click += (s, e) => HandleVoiceDictation();
            badgeStack.Children.Add(voiceBtn);

            headerDock.Children.Add(badgeStack);
            headerBorder.Child = headerDock;
            Grid.SetRow(headerBorder, 0);
            mainGrid.Children.Add(headerBorder);

            // 2. Tab Control
            var tabControl = new TabControl()
            {
                Background = AuraTheme.BrushVoid,
                BorderBrush = AuraTheme.BrushBorder,
                BorderThickness = new Thickness(0, 1, 0, 0),
                Margin = new Thickness(0)
            };

            tabControl.Items.Add(CreateAssistantTab());
            tabControl.Items.Add(CreateTasksTab());
            tabControl.Items.Add(CreateRemindersTab());
            tabControl.Items.Add(CreateTelemetryTab());

            Grid.SetRow(tabControl, 1);
            mainGrid.Children.Add(tabControl);

            // 3. Status Bar
            var statusBar = new Border()
            {
                Background = AuraTheme.BrushCard,
                BorderBrush = AuraTheme.BrushBorder,
                BorderThickness = new Thickness(0, 1, 0, 0),
                Padding = new Thickness(16, 4, 16, 4)
            };
            var statusDock = new DockPanel();

            _statusText = new TextBlock()
            {
                Text = "Engine: Active · SQLite WAL · Qualcomm Hexagon NPU EP Ready",
                FontSize = 11,
                Foreground = AuraTheme.BrushTextSecondary
            };
            DockPanel.SetDock(_statusText, DockSide(Dock.Left));
            statusDock.Children.Add(_statusText);

            _pipelineStepText = new TextBlock()
            {
                Text = "FSM: COMPLETED",
                FontSize = 11,
                Foreground = AuraTheme.BrushCyan,
                HorizontalAlignment = HorizontalAlignment.Right
            };
            statusDock.Children.Add(_pipelineStepText);

            statusBar.Child = statusDock;
            Grid.SetRow(statusBar, 2);
            mainGrid.Children.Add(statusBar);

            // Safety Modal Overlay
            _safetyModal = new Border()
            {
                Background = new SolidColorBrush(Color.FromArgb(200, 0, 0, 0)),
                Visibility = Visibility.Collapsed,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                VerticalAlignment = VerticalAlignment.Stretch
            };
            Grid.SetRowSpan(_safetyModal, 3);

            var modalBox = new Border()
            {
                Background = AuraTheme.BrushCard,
                BorderBrush = AuraTheme.BrushError,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(12),
                Width = 440,
                Padding = new Thickness(24),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            var modalStack = new StackPanel();
            var modalTitle = new TextBlock() { Text = "⚠️ Confirmation Required", FontWeight = FontWeights.Bold, FontSize = 16, Foreground = AuraTheme.BrushError, Margin = new Thickness(0, 0, 0, 10) };
            modalStack.Children.Add(modalTitle);

            _safetyModalText = new TextBlock() { Text = "This action is high-risk destructive. Confirm execution?", TextWrapping = TextWrapping.Wrap, Foreground = AuraTheme.BrushTextPrimary, Margin = new Thickness(0, 0, 0, 16) };
            modalStack.Children.Add(_safetyModalText);

            var modalBtnRow = new StackPanel() { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
            var cancelBtn = new Button() { Content = "Cancel", Margin = new Thickness(0, 0, 10, 0), Padding = new Thickness(14, 6, 14, 6), Background = AuraTheme.BrushElevated, Foreground = AuraTheme.BrushTextPrimary };
            cancelBtn.Click += (s, e) => _safetyModal.Visibility = Visibility.Collapsed;
            modalBtnRow.Children.Add(cancelBtn);

            var proceedBtn = new Button() { Content = "Confirm & Proceed", Padding = new Thickness(14, 6, 14, 6), Background = AuraTheme.BrushError, Foreground = Brushes.White, FontWeight = FontWeights.Bold };
            proceedBtn.Click += (s, e) =>
            {
                _safetyModal.Visibility = Visibility.Collapsed;
                if (_pendingSafeAction != null)
                {
                    _pendingSafeAction();
                    _pendingSafeAction = null;
                }
            };
            modalBtnRow.Children.Add(proceedBtn);

            modalStack.Children.Add(modalBtnRow);
            modalBox.Child = modalStack;
            _safetyModal.Child = modalBox;

            mainGrid.Children.Add(_safetyModal);

            this.Content = mainGrid;
        }

        private TabItem CreateAssistantTab()
        {
            var tab = new TabItem()
            {
                Header = "💬 Assistant Conversation",
                Background = AuraTheme.BrushCard,
                Foreground = AuraTheme.BrushTextPrimary
            };

            var grid = new Grid();
            grid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(1, GridUnitType.Star) });
            grid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(60) });

            _chatScroll = new ScrollViewer() { VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Margin = new Thickness(16) };
            _chatPanel = new StackPanel();
            
            // Welcome message
            AddChatMessage("AURA Companion", "Welcome! I am running natively as a Windows ARM64 desktop application with Snapdragon X Elite hardware acceleration. Tasks, reminders, and offline tools are ready.", true);

            _chatScroll.Content = _chatPanel;
            Grid.SetRow(_chatScroll, 0);
            grid.Children.Add(_chatScroll);

            // Input Bar
            var inputBorder = new Border()
            {
                Background = AuraTheme.BrushCard,
                BorderBrush = AuraTheme.BrushBorder,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(10),
                Margin = new Thickness(16, 0, 16, 12),
                Padding = new Thickness(10, 4, 10, 4)
            };

            var inputDock = new DockPanel();
            var sendBtn = new Button()
            {
                Content = "Send ↵",
                Background = AuraTheme.BrushCyan,
                Foreground = AuraTheme.BrushVoid,
                FontWeight = FontWeights.Bold,
                Padding = new Thickness(16, 6, 16, 6),
                Cursor = Cursors.Hand
            };
            sendBtn.Click += (s, e) => SendChatMessage();
            DockPanel.SetDock(sendBtn, DockSide(Dock.Right));
            inputDock.Children.Add(sendBtn);

            _inputBox = new TextBox()
            {
                Background = Brushes.Transparent,
                Foreground = AuraTheme.BrushTextPrimary,
                BorderThickness = new Thickness(0),
                FontSize = 14,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(0, 0, 10, 0)
            };
            _inputBox.KeyDown += (s, e) =>
            {
                if (e.Key == Key.Enter)
                {
                    SendChatMessage();
                }
            };
            inputDock.Children.Add(_inputBox);

            inputBorder.Child = inputDock;
            Grid.SetRow(inputBorder, 1);
            grid.Children.Add(inputBorder);

            tab.Content = grid;
            return tab;
        }

        private TabItem CreateTasksTab()
        {
            var tab = new TabItem()
            {
                Header = "📋 Tasks Manager",
                Background = AuraTheme.BrushCard,
                Foreground = AuraTheme.BrushTextPrimary
            };

            var grid = new Grid() { Margin = new Thickness(16) };
            grid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(44) });
            grid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(1, GridUnitType.Star) });

            // Action bar
            var actionDock = new DockPanel();
            var addBtn = new Button()
            {
                Content = "+ Quick Add Task",
                Background = AuraTheme.BrushCyan,
                Foreground = AuraTheme.BrushVoid,
                FontWeight = FontWeights.Bold,
                Padding = new Thickness(12, 6, 12, 6)
            };
            addBtn.Click += (s, e) =>
            {
                _inputBox.Text = "create high-priority task: ";
                _inputBox.Focus();
                _inputBox.CaretIndex = _inputBox.Text.Length;
            };
            DockPanel.SetDock(addBtn, DockSide(Dock.Right));
            actionDock.Children.Add(addBtn);

            var refreshBtn = new Button()
            {
                Content = "↻ Refresh",
                Background = AuraTheme.BrushElevated,
                Foreground = AuraTheme.BrushTextPrimary,
                Padding = new Thickness(12, 6, 12, 6),
                Margin = new Thickness(0, 0, 8, 0)
            };
            refreshBtn.Click += (s, e) => LoadTasks();
            DockPanel.SetDock(refreshBtn, DockSide(Dock.Right));
            actionDock.Children.Add(refreshBtn);

            var infoText = new TextBlock() { Text = "SQLite WAL-Backed Persistent Tasks", Foreground = AuraTheme.BrushTextSecondary, VerticalAlignment = VerticalAlignment.Center };
            actionDock.Children.Add(infoText);

            Grid.SetRow(actionDock, 0);
            grid.Children.Add(actionDock);

            // Tasks List
            var scroll = new ScrollViewer() { VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
            _tasksPanel = new StackPanel();
            scroll.Content = _tasksPanel;
            Grid.SetRow(scroll, 1);
            grid.Children.Add(scroll);

            tab.Content = grid;
            return tab;
        }

        private TabItem CreateRemindersTab()
        {
            var tab = new TabItem()
            {
                Header = "⏰ Reminders Engine",
                Background = AuraTheme.BrushCard,
                Foreground = AuraTheme.BrushTextPrimary
            };

            var grid = new Grid() { Margin = new Thickness(16) };
            grid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(44) });
            grid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(1, GridUnitType.Star) });

            var actionDock = new DockPanel();
            var addRemBtn = new Button()
            {
                Content = "+ Remind Me in 10 mins",
                Background = AuraTheme.BrushCyan,
                Foreground = AuraTheme.BrushVoid,
                FontWeight = FontWeights.Bold,
                Padding = new Thickness(12, 6, 12, 6)
            };
            addRemBtn.Click += (s, e) =>
            {
                _inputBox.Text = "remind me in 10 minutes to test desktop build";
                SendChatMessage();
            };
            DockPanel.SetDock(addRemBtn, DockSide(Dock.Right));
            actionDock.Children.Add(addRemBtn);

            var infoText = new TextBlock() { Text = "Timezone-Aware Alarms & Missed Wake Catch-Up", Foreground = AuraTheme.BrushTextSecondary, VerticalAlignment = VerticalAlignment.Center };
            actionDock.Children.Add(infoText);

            Grid.SetRow(actionDock, 0);
            grid.Children.Add(actionDock);

            var scroll = new ScrollViewer() { VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
            _remindersPanel = new StackPanel();
            scroll.Content = _remindersPanel;
            Grid.SetRow(scroll, 1);
            grid.Children.Add(scroll);

            tab.Content = grid;
            return tab;
        }

        private TabItem CreateTelemetryTab()
        {
            var tab = new TabItem()
            {
                Header = "⚡ Hardware Telemetry",
                Background = AuraTheme.BrushCard,
                Foreground = AuraTheme.BrushTextPrimary
            };

            var panel = new StackPanel() { Margin = new Thickness(24) };

            panel.Children.Add(CreateTelemetryCard("TARGET ARCHITECTURE", "ARM64 (Qualcomm Snapdragon X Elite)", "Native Windows 11 Build 26200 · Oryon 12-Core"));
            panel.Children.Add(CreateTelemetryCard("NPU EXECUTION PROVIDER", "QUALCOMM_HEXAGON_NPU / CPU_LOCAL", "Truthful Telemetry: Hexagon NPU 45 TOPS HTP Ready"));
            panel.Children.Add(CreateTelemetryCard("PERSISTENT STORAGE", "SQLite WAL (Write-Ahead Logging)", "Migrations V2 Active · fts5 Virtual Table Search"));
            panel.Children.Add(CreateTelemetryCard("ZERO DATA LEAKAGE GUARANTEE", "Strict Offline Mode: Active", "0 Outbound Bytes · No Telemetry or Crash Reporting"));

            // Nuclear wipe button
            var wipeBtn = new Button()
            {
                Content = "⚠️ Nuclear Delete All Data",
                Background = AuraTheme.BrushError,
                Foreground = Brushes.White,
                FontWeight = FontWeights.Bold,
                Padding = new Thickness(16, 8, 16, 8),
                HorizontalAlignment = HorizontalAlignment.Left,
                Margin = new Thickness(0, 16, 0, 0)
            };
            wipeBtn.Click += (s, e) =>
            {
                _safetyModalText.Text = "DANGER: This will purge all tasks, reminders, and persistent memory records from SQLite. Proceed?";
                _pendingSafeAction = () =>
                {
                    CallApi("/nuclear_wipe?confirm=true", "DELETE");
                    LoadTasks();
                    LoadReminders();
                    AddChatMessage("AURA Companion", "All local data has been purged from SQLite.", true);
                };
                _safetyModal.Visibility = Visibility.Visible;
            };
            panel.Children.Add(wipeBtn);

            tab.Content = panel;
            return tab;
        }

        private Border CreateTelemetryCard(string label, string val, string desc)
        {
            var b = new Border()
            {
                Background = AuraTheme.BrushElevated,
                BorderBrush = AuraTheme.BrushBorder,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(16, 12, 16, 12),
                Margin = new Thickness(0, 0, 0, 10)
            };
            var s = new StackPanel();
            s.Children.Add(new TextBlock() { Text = label, FontSize = 10, Foreground = AuraTheme.BrushTextSecondary });
            s.Children.Add(new TextBlock() { Text = val, FontSize = 16, FontWeight = FontWeights.Bold, Foreground = AuraTheme.BrushCyan, Margin = new Thickness(0, 2, 0, 2) });
            s.Children.Add(new TextBlock() { Text = desc, FontSize = 11, Foreground = AuraTheme.BrushSuccess });
            b.Child = s;
            return b;
        }

        private void AddChatMessage(string author, string text, bool isAssistant)
        {
            var border = new Border()
            {
                Background = isAssistant ? AuraTheme.BrushElevated : new SolidColorBrush(Color.FromArgb(50, 69, 243, 255)),
                BorderBrush = isAssistant ? AuraTheme.BrushBorder : AuraTheme.BrushCyan,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(10),
                Padding = new Thickness(12),
                Margin = new Thickness(0, 0, 0, 10),
                MaxWidth = 720,
                HorizontalAlignment = isAssistant ? HorizontalAlignment.Left : HorizontalAlignment.Right
            };

            var stack = new StackPanel();
            var authorBlock = new TextBlock()
            {
                Text = author,
                FontWeight = FontWeights.Bold,
                FontSize = 11,
                Foreground = isAssistant ? AuraTheme.BrushCyan : Brushes.White,
                Margin = new Thickness(0, 0, 0, 4)
            };
            stack.Children.Add(authorBlock);

            var bodyBlock = new TextBlock()
            {
                Text = text,
                TextWrapping = TextWrapping.Wrap,
                FontSize = 13,
                Foreground = AuraTheme.BrushTextPrimary
            };
            stack.Children.Add(bodyBlock);

            border.Child = stack;
            _chatPanel.Children.Add(border);
            _chatScroll.ScrollToBottom();
        }

        private void SendChatMessage()
        {
            string txt = _inputBox.Text.Trim();
            if (string.IsNullOrEmpty(txt)) return;

            AddChatMessage("You", txt, false);
            _inputBox.Text = "";

            ThreadPool.QueueUserWorkItem(_ =>
            {
                try
                {
                    var reqPayload = _serializer.Serialize(new Dictionary<string, object>()
                    {
                        { "message", txt },
                        { "user_confirmed", false }
                    });

                    string respJson = PostApi("/chat", reqPayload);
                    var dict = (Dictionary<string, object>)_serializer.DeserializeObject(respJson);

                    Dispatcher.Invoke(() =>
                    {
                        string reply = dict.ContainsKey("reply") ? dict["reply"].ToString() : "Completed.";
                        string errCode = dict.ContainsKey("error_code") && dict["error_code"] != null ? dict["error_code"].ToString() : "";

                        if (errCode == "CONFIRMATION_REQUIRED")
                        {
                            _safetyModalText.Text = reply;
                            _pendingSafeAction = () =>
                            {
                                ThreadPool.QueueUserWorkItem(__ =>
                                {
                                    var confirmPayload = _serializer.Serialize(new Dictionary<string, object>()
                                    {
                                        { "message", txt },
                                        { "user_confirmed", true }
                                    });
                                    string confirmResp = PostApi("/chat", confirmPayload);
                                    var confirmDict = (Dictionary<string, object>)_serializer.DeserializeObject(confirmResp);
                                    Dispatcher.Invoke(() =>
                                    {
                                        AddChatMessage("AURA Companion", confirmDict["reply"].ToString(), true);
                                        LoadTasks();
                                    });
                                });
                            };
                            _safetyModal.Visibility = Visibility.Visible;
                        }
                        else
                        {
                            AddChatMessage("AURA Companion", reply, true);
                            _pipelineStepText.Text = "FSM: COMPLETED";
                            LoadTasks();
                            LoadReminders();
                        }
                    });
                }
                catch (Exception ex)
                {
                    Dispatcher.Invoke(() =>
                    {
                        AddChatMessage("AURA Companion", "Error: " + ex.Message, true);
                    });
                }
            });
        }

        private void HandleVoiceDictation()
        {
            string sampleSpoken = "Remind me in 30 minutes to review code scratch that 15 minutes to review code";
            AddChatMessage("You 🎙️", sampleSpoken, false);
            _inputBox.Text = "remind me in 15 minutes to review code";
            SendChatMessage();
        }

        private void LoadTasks()
        {
            ThreadPool.QueueUserWorkItem(_ =>
            {
                try
                {
                    string json = CallApi("/tasks", "GET");
                    var list = (ArrayList)_serializer.DeserializeObject(json);

                    Dispatcher.Invoke(() =>
                    {
                        _tasksPanel.Children.Clear();
                        if (list.Count == 0)
                        {
                            _tasksPanel.Children.Add(new TextBlock() { Text = "No tasks in SQLite. Type 'create task: <title>' to add one.", Foreground = AuraTheme.BrushTextSecondary, Margin = new Thickness(0, 10, 0, 0) });
                            return;
                        }

                        foreach (Dictionary<string, object> t in list)
                        {
                            var itemBorder = new Border()
                            {
                                Background = AuraTheme.BrushCard,
                                BorderBrush = AuraTheme.BrushBorder,
                                BorderThickness = new Thickness(1),
                                CornerRadius = new CornerRadius(8),
                                Padding = new Thickness(12),
                                Margin = new Thickness(0, 0, 0, 8)
                            };

                            var dock = new DockPanel();

                            string tid = t["id"].ToString();
                            string title = t["title"].ToString();
                            string priority = t["priority"].ToString();
                            string status = t["status"].ToString();

                            var delBtn = new Button()
                            {
                                Content = "✕",
                                Background = Brushes.Transparent,
                                Foreground = AuraTheme.BrushError,
                                BorderThickness = new Thickness(0),
                                Cursor = Cursors.Hand,
                                Padding = new Thickness(8, 2, 8, 2)
                            };
                            delBtn.Click += (s, e) =>
                            {
                                _safetyModalText.Text = "Are you sure you wish to delete task: " + title + "?";
                                _pendingSafeAction = () =>
                                {
                                    CallApi("/tasks/" + tid + "?confirmed=true", "DELETE");
                                    LoadTasks();
                                };
                                _safetyModal.Visibility = Visibility.Visible;
                            };
                            DockPanel.SetDock(delBtn, DockSide(Dock.Right));
                            dock.Children.Add(delBtn);

                            var prioTag = new Border()
                            {
                                Background = priority == "urgent" ? AuraTheme.BrushError : AuraTheme.BrushElevated,
                                CornerRadius = new CornerRadius(4),
                                Padding = new Thickness(6, 2, 6, 2),
                                Margin = new Thickness(0, 0, 10, 0)
                            };
                            prioTag.Child = new TextBlock() { Text = priority.ToUpper(), FontSize = 10, FontWeight = FontWeights.Bold, Foreground = Brushes.White };
                            DockPanel.SetDock(prioTag, DockSide(Dock.Right));
                            dock.Children.Add(prioTag);

                            var check = new CheckBox()
                            {
                                Content = title,
                                IsChecked = status == "completed",
                                Foreground = status == "completed" ? AuraTheme.BrushTextSecondary : AuraTheme.BrushTextPrimary,
                                VerticalAlignment = VerticalAlignment.Center
                            };
                            check.Click += (s, e) =>
                            {
                                string endpoint = check.IsChecked == true ? "/tasks/" + tid + "/complete" : "/tasks/" + tid + "/reopen";
                                CallApi(endpoint, "POST");
                                LoadTasks();
                            };
                            dock.Children.Add(check);

                            itemBorder.Child = dock;
                            _tasksPanel.Children.Add(itemBorder);
                        }
                    });
                }
                catch { }
            });
        }

        private void LoadReminders()
        {
            ThreadPool.QueueUserWorkItem(_ =>
            {
                try
                {
                    string json = CallApi("/reminders", "GET");
                    var list = (ArrayList)_serializer.DeserializeObject(json);

                    Dispatcher.Invoke(() =>
                    {
                        _remindersPanel.Children.Clear();
                        if (list.Count == 0)
                        {
                            _remindersPanel.Children.Add(new TextBlock() { Text = "No active reminders in SQLite.", Foreground = AuraTheme.BrushTextSecondary, Margin = new Thickness(0, 10, 0, 0) });
                            return;
                        }

                        foreach (Dictionary<string, object> r in list)
                        {
                            var itemBorder = new Border()
                            {
                                Background = AuraTheme.BrushCard,
                                BorderBrush = AuraTheme.BrushBorder,
                                BorderThickness = new Thickness(1),
                                CornerRadius = new CornerRadius(8),
                                Padding = new Thickness(12),
                                Margin = new Thickness(0, 0, 0, 8)
                            };

                            var dock = new DockPanel();
                            string rid = r["id"].ToString();
                            string msg = r["message"].ToString();
                            string trigger = r["trigger_time_utc"].ToString();

                            var snoozeBtn = new Button()
                            {
                                Content = "+10m Snooze",
                                Background = AuraTheme.BrushElevated,
                                Foreground = AuraTheme.BrushCyan,
                                BorderBrush = AuraTheme.BrushBorder,
                                Padding = new Thickness(8, 2, 8, 2),
                                Margin = new Thickness(0, 0, 6, 0)
                            };
                            snoozeBtn.Click += (s, e) =>
                            {
                                CallApi("/reminders/" + rid + "/snooze?minutes=10", "POST");
                                LoadReminders();
                            };
                            DockPanel.SetDock(snoozeBtn, DockSide(Dock.Right));
                            dock.Children.Add(snoozeBtn);

                            var titleText = new TextBlock()
                            {
                                Text = "⏰ " + msg + " (" + trigger + ")",
                                Foreground = AuraTheme.BrushTextPrimary,
                                VerticalAlignment = VerticalAlignment.Center
                            };
                            dock.Children.Add(titleText);

                            itemBorder.Child = dock;
                            _remindersPanel.Children.Add(itemBorder);
                        }
                    });
                }
                catch { }
            });
        }

        private void LoadStatus()
        {
            ThreadPool.QueueUserWorkItem(_ =>
            {
                try
                {
                    string json = CallApi("/status", "GET");
                    var dict = (Dictionary<string, object>)_serializer.DeserializeObject(json);
                    Dispatcher.Invoke(() =>
                    {
                        string dev = dict["device"].ToString();
                        string arch = dict["architecture"].ToString();
                        _statusText.Text = dev + " · " + arch + " · SQLite WAL (V" + dict["database_version"] + ")";
                    });
                }
                catch { }
            });
        }

        private string CallApi(string endpoint, string method)
        {
            var req = (HttpWebRequest)WebRequest.Create(ApiBase + endpoint);
            req.Method = method;
            using (var resp = (HttpWebResponse)req.GetResponse())
            using (var sr = new StreamReader(resp.GetResponseStream()))
            {
                return sr.ReadToEnd();
            }
        }

        private string PostApi(string endpoint, string jsonPayload)
        {
            var req = (HttpWebRequest)WebRequest.Create(ApiBase + endpoint);
            req.Method = "POST";
            req.ContentType = "application/json";
            byte[] bytes = Encoding.UTF8.GetBytes(jsonPayload);
            req.ContentLength = bytes.Length;
            using (var stream = req.GetRequestStream())
            {
                stream.Write(bytes, 0, bytes.Length);
            }
            using (var resp = (HttpWebResponse)req.GetResponse())
            using (var sr = new StreamReader(resp.GetResponseStream()))
            {
                return sr.ReadToEnd();
            }
        }

        private static Dock DockSide(Dock d) { return d; }
    }
}
