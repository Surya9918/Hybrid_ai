using Microsoft.UI.Xaml;
using System;
using AuraCompanion.UI.Views;

namespace AuraCompanion
{
    public partial class App : Application
    {
        private OrbWindow? _orbWindow;
        private HudWindow? _hudWindow;

        public App()
        {
            this.InitializeComponent();
        }

        protected override void OnLaunched(Microsoft.UI.Xaml.LaunchActivatedEventArgs args)
        {
            _orbWindow = new OrbWindow();
            _orbWindow.Activate();

            _hudWindow = new HudWindow();
            _hudWindow.Activate();
        }
    }
}
