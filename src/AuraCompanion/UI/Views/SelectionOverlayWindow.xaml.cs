using Microsoft.UI.Xaml;
using System;

namespace AuraCompanion.UI.Views
{
    public sealed partial class SelectionOverlayWindow : Window
    {
        public SelectionOverlayWindow()
        {
            this.InitializeComponent();
            var appWindow = this.AppWindow;
            if (appWindow != null)
            {
                // Fullscreen overlay on active display
                appWindow.TitleBar.ExtendsContentIntoTitleBar = true;
            }
        }
    }
}
