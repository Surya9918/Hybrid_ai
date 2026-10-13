using Microsoft.UI.Xaml;
using System;

namespace AuraCompanion.UI.Views
{
    public sealed partial class SettingsWindow : Window
    {
        public SettingsWindow()
        {
            this.InitializeComponent();
            var appWindow = this.AppWindow;
            if (appWindow != null)
            {
                appWindow.Resize(new Windows.Graphics.SizeInt32(640, 540));
            }
        }
    }
}
