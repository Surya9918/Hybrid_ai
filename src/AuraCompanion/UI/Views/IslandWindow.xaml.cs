using Microsoft.UI.Xaml;
using System;

namespace AuraCompanion.UI.Views
{
    public sealed partial class IslandWindow : Window
    {
        public IslandWindow()
        {
            this.InitializeComponent();
            var appWindow = this.AppWindow;
            if (appWindow != null)
            {
                appWindow.Resize(new Windows.Graphics.SizeInt32(500, 400));
                appWindow.TitleBar.ExtendsContentIntoTitleBar = true;
            }
        }
    }
}
