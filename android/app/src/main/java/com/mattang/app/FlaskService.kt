package com.mattang.app

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class FlaskService : Service() {
    private var py: Python? = null
    private var flaskModule: Any? = null

    override fun onCreate() {
        super.onCreate()
        try {
            if (!Python.isStarted()) {
                Python.start(AndroidPlatform(this))
            }
            py = Python.getInstance()
            flaskModule = py?.getModule("Mattang")
            Log.d("FlaskService", "Python environment initialized")
        } catch (e: Exception) {
            Log.e("FlaskService", "Failed to initialize Python", e)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        try {
            flaskModule?.callAttr("run_server")
            Log.d("FlaskService", "Flask server started")
        } catch (e: Exception) {
            Log.e("FlaskService", "Failed to start Flask server", e)
        }
        return START_STICKY
    }

    override fun onDestroy() {
        try {
            flaskModule?.callAttr("stop_server")
            Log.d("FlaskService", "Flask server stopped")
        } catch (e: Exception) {
            Log.e("FlaskService", "Failed to stop Flask server", e)
        }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
} 