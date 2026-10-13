using Microsoft.UI.Xaml;
using System;

namespace AuraCompanion.UI.Views
{
    public sealed partial class LauncherWindow : Window
    {
        public LauncherWindow()
        {
            this.InitializeComponent();
            var appWindow = this.AppWindow;
            if (appWindow != null)
            {
                appWindow.Resize(new Windows.Graphics.SizeInt32(540, 400));
                appWindow.TitleBar.ExtendsContentIntoTitleBar = true;
            }
        }
    }
}
