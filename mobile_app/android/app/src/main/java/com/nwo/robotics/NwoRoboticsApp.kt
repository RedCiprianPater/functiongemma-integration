package com.nwo.robotics

import android.app.Application
import android.util.Log

/**
 * Application class for NWO Robotics
 */
class NwoRoboticsApp : Application() {
    
    companion object {
        private const val TAG = "NwoRoboticsApp"
        lateinit var instance: NwoRoboticsApp
            private set
    }
    
    override fun onCreate() {
        super.onCreate()
        instance = this
        Log.i(TAG, "NWO Robotics App initialized")
    }
}
