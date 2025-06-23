package com.mattang.app

import android.content.Intent
import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Flask 서비스 시작
        startService(Intent(this, FlaskService::class.java))

        // WebView 설정
        webView = findViewById(R.id.webView)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            setSupportZoom(true)
        }

        webView.webViewClient = WebViewClient()
        webView.loadUrl("http://localhost:5000")
    }

    override fun onDestroy() {
        // 앱 종료 시 Flask 서비스 중지
        stopService(Intent(this, FlaskService::class.java))
        super.onDestroy()
    }
} 