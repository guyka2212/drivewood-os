plugins {
    id("com.android.application")
}

android {
    namespace = "org.drivewood.link"
    compileSdk = 37
    defaultConfig {
        applicationId = "org.drivewood.link"
        minSdk = 29
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
