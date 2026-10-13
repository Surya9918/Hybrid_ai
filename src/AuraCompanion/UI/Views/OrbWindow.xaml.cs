using Microsoft.UI.Xaml;
using System;
using AuraCompanion.Design;

namespace AuraCompanion.UI.Views
{
    public enum OrbVisualState
    {
        Idle,
        Listening,
        Thinking,
        Speaking,
        Error
    }

    public sealed partial class OrbWindow : Window
    {
        private OrbVisualState _currentState = OrbVisualState.Idle;

        public OrbWindow()
        {
            this.InitializeComponent();
            ApplyHitodamaWindowStyling();
            SetVisualState(OrbVisualState.Idle);
        }

        private void ApplyHitodamaWindowStyling()
        {
            // Transparent borderless floating composition window
            var appWindow = this.AppWindow;
            if (appWindow != null)
            {
                appWindow.Resize(new Windows.Graphics.SizeInt32(96, 96));
                appWindow.TitleBar.ExtendsContentIntoTitleBar = true;
            }
        }

        public void SetVisualState(OrbVisualState state)
        {
            _currentState = state;
            switch (state)
            {
                case OrbVisualState.Idle:
                    GlowEllipse.Fill = new Microsoft.UI.Xaml.Media.SolidColorBrush(
                        Windows.UI.Color.FromArgb(115, 102, 252, 241));
                    GlowEllipse.Opacity = 0.45;
                    break;
                case OrbVisualState.Listening:
                    // Pulse brighter cyan with active listening aura
                    GlowEllipse.Fill = new Microsoft.UI.Xaml.Media.SolidColorBrush(
                        Windows.UI.Color.FromArgb(200, 69, 243, 255));
                    GlowEllipse.Opacity = 0.85;
                    break;
                case OrbVisualState.Thinking:
                    // Rapid rotating hue
                    GlowEllipse.Opacity = 0.65;
                    break;
                case OrbVisualState.Speaking:
                    GlowEllipse.Opacity = 0.75;
                    break;
                case OrbVisualState.Error:
                    GlowEllipse.Fill = new Microsoft.UI.Xaml.Media.SolidColorBrush(
                        Windows.UI.Color.FromArgb(200, 255, 78, 100));
                    break;
            }
        }
    }
}
