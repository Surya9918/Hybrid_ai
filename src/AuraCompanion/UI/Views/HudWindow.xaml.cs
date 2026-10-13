using Microsoft.UI.Xaml;
using System;

namespace AuraCompanion.UI.Views
{
    public sealed partial class HudWindow : Window
    {
        public HudWindow()
        {
            this.InitializeComponent();
            var appWindow = this.AppWindow;
            if (appWindow != null)
            {
                appWindow.Resize(new Windows.Graphics.SizeInt32(380, 96));
                appWindow.TitleBar.ExtendsContentIntoTitleBar = true;
            }
        }

        public void UpdateStatus(string title, string subtitle, string colorHex = "#45F3FF")
        {
            TitleText.Text = title;
            SubtitleText.Text = subtitle;
            // Update color
        }
    }
}
