package com.krishitwin.samsaari

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle

import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts

import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView

import androidx.compose.animation.Crossfade
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

import androidx.core.content.ContextCompat

import kotlinx.coroutines.delay

import java.io.File

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SamsaariApp()
        }
    }
}

/* ---------------------------------------------------------
   SCREEN STATE & APP ROUTER
--------------------------------------------------------- */
private enum class Screen {
    Splash, Dashboard, Camera, Decision, AudioPlay, History, Settings
}

@Composable
fun SamsaariApp() {
    var screen by remember { mutableStateOf(Screen.Splash) }

    Crossfade(targetState = screen, label = "AppRouter") { currentScreen ->
        when (currentScreen) {
            Screen.Splash -> SplashScreen(onFinished = { screen = Screen.Dashboard })
            Screen.Dashboard -> DashboardScreen(
                onScanCrop = { screen = Screen.Camera },
                onDecision = { screen = Screen.Decision },
                onAudio = { screen = Screen.AudioPlay },
                onHistory = { screen = Screen.History },
                onSettings = { screen = Screen.Settings }
            )
            Screen.Camera -> CropScanScreen(
                onBack = { screen = Screen.Dashboard },
                onAnalysisComplete = { screen = Screen.Decision }
            )
            Screen.Decision -> PlaceholderScreen("Decision (Scenario A vs B)", onClick = { screen = Screen.Dashboard })
            Screen.AudioPlay -> PlaceholderScreen("Audio Advisory", onClick = { screen = Screen.Dashboard })
            Screen.History -> PlaceholderScreen("History", onClick = { screen = Screen.Dashboard })
            Screen.Settings -> PlaceholderScreen("Settings", onClick = { screen = Screen.Dashboard })
        }
    }
}

/* ---------------------------------------------------------
   THEME & SHARED BACKGROUND
--------------------------------------------------------- */
val Emerald500 = Color(0xFF10B981)
val Emerald800 = Color(0xFF065F46)
val EmeraldDark = Color(0xFF044231)
val MintAccent = Color(0xFFA8E8DE)
val AlertCoral = Color(0xFFFF8A8A)
val CardBackground = Color.White.copy(alpha = 0.12f)
val CardBorder = Color.White.copy(alpha = 0.20f)

@Composable
fun SamsaariBackground(content: @Composable () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.linearGradient(
                    colors = listOf(Emerald500, Emerald800, EmeraldDark),
                    start = Offset(0f, 0f),
                    end = Offset(1100f, 1600f)
                )
            )
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val diagonalPath = Path().apply {
                moveTo(-size.width * 0.20f, size.height * 0.45f)
                lineTo(size.width * 0.02f, size.height * 0.38f)
                lineTo(size.width * 0.78f, size.height)
                lineTo(size.width * 0.56f, size.height)
                close()
            }
            drawPath(
                path = diagonalPath,
                brush = Brush.linearGradient(
                    colors = listOf(Color.Transparent, Color(0x22FFFFFF), Color(0x11FFFFFF), Color.Transparent),
                    start = Offset(0f, size.height * 0.40f),
                    end = Offset(size.width * 0.80f, size.height)
                )
            )
        }
        content()
    }
}

/* ---------------------------------------------------------
   DASHBOARD SCREEN
--------------------------------------------------------- */
@Composable
fun DashboardScreen(
    onScanCrop: () -> Unit,
    onDecision: () -> Unit,
    onAudio: () -> Unit,
    onHistory: () -> Unit,
    onSettings: () -> Unit
) {
    SamsaariBackground {
        Column(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier
                    .weight(1f)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(modifier = Modifier.height(56.dp))
                DashboardHeader()
                Spacer(modifier = Modifier.height(24.dp))
                AlertCard(onScanCrop)
                Spacer(modifier = Modifier.height(16.dp))
                ActiveFieldCard()
                Spacer(modifier = Modifier.height(16.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Box(modifier = Modifier.weight(1f)) { CropHealthCard() }
                    Box(modifier = Modifier.weight(1f)) { WeatherCard() }
                }
                Spacer(modifier = Modifier.height(24.dp))
                
                // Updated Explicit Quick Actions
                QuickActions(onScanCrop, onDecision, onAudio)
                
                Spacer(modifier = Modifier.height(24.dp))
                RecentDecisionsList()
                Spacer(modifier = Modifier.height(32.dp))
            }
            
            // Updated Tab Bar Navigation
            SamsaariBottomNav(
                onHistory = onHistory,
                onSettings = onSettings
            )
        }
    }
}

@Composable
fun DashboardHeader() {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column {
            Text("Samsaari", color = Color.White, fontSize = 32.sp, fontFamily = FontFamily.Serif)
            Text("Good morning, Farmer", color = Color.White.copy(alpha = 0.8f), fontSize = 16.sp)
        }
        Box(modifier = Modifier.size(44.dp).clip(CircleShape).background(MintAccent), contentAlignment = Alignment.Center) {
            Icon(Icons.Default.Person, contentDescription = "Profile", tint = Emerald800)
        }
    }
}

@Composable
fun AlertCard(onScanCrop: () -> Unit) {
    Box(
        modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(AlertCoral.copy(0.15f)).border(1.dp, AlertCoral.copy(0.4f), RoundedCornerShape(20.dp)).padding(16.dp)
    ) {
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Warning, contentDescription = "Warning", tint = AlertCoral, modifier = Modifier.size(20.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Crop needs attention", color = AlertCoral, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text("Possible Leaf Blight detected.", color = Color.White, fontSize = 14.sp)
            }
            Button(onClick = onScanCrop, colors = ButtonDefaults.buttonColors(containerColor = AlertCoral), shape = RoundedCornerShape(12.dp)) {
                Text("Analyze", color = EmeraldDark, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
fun ActiveFieldCard() {
    GlassCard {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column {
                Text("My Tomato Field", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                Text("Crop: Tomato  •  Area: 2 acres", color = Color.White.copy(0.7f), fontSize = 14.sp)
                Spacer(modifier = Modifier.height(12.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.LocationOn, contentDescription = "Location", tint = MintAccent, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Madurai District", color = MintAccent, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                }
            }
            Box(modifier = Modifier.size(64.dp).clip(RoundedCornerShape(14.dp)).background(Color.White.copy(0.2f)), contentAlignment = Alignment.Center) {
                Icon(Icons.Default.Place, contentDescription = "Map", tint = Color.White, modifier = Modifier.size(32.dp))
            }
        }
    }
}

@Composable
fun CropHealthCard() {
    GlassCard(modifier = Modifier.fillMaxHeight()) {
        Column {
            Text("Crop Health", color = Color.White.copy(0.8f), fontSize = 14.sp)
            Text("Needs Attention", color = AlertCoral, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(16.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                CircularProgressIndicator(progress = { 0.37f }, modifier = Modifier.size(32.dp), color = AlertCoral, trackColor = Color.White.copy(0.2f), strokeWidth = 4.dp)
                Spacer(modifier = Modifier.width(12.dp))
                Text("NDVI: 0.37\nUpdated Today", color = Color.White.copy(0.7f), fontSize = 12.sp, lineHeight = 16.sp)
            }
        }
    }
}

@Composable
fun WeatherCard() {
    GlassCard(modifier = Modifier.fillMaxHeight()) {
        Column {
            Text("Weather", color = Color.White.copy(0.8f), fontSize = 14.sp)
            Text("29°C", color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text("Partly Cloudy", color = Color.White, fontSize = 14.sp, fontWeight = FontWeight.Medium)
            Text("Rain: 40% • Wind: 12km/h", color = Color.White.copy(0.7f), fontSize = 12.sp)
        }
    }
}

@Composable
fun QuickActions(onScanCrop: () -> Unit, onDecision: () -> Unit, onAudio: () -> Unit) {
    Text("Quick Actions", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
    Spacer(modifier = Modifier.height(12.dp))
    Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        
        // Action 1: Scan Crop
        Button(
            onClick = onScanCrop, 
            modifier = Modifier.fillMaxWidth().height(72.dp), 
            colors = ButtonDefaults.buttonColors(containerColor = MintAccent), 
            shape = RoundedCornerShape(16.dp)
        ) {
            Icon(Icons.Default.Search, contentDescription = "Scan", tint = EmeraldDark)
            Spacer(modifier = Modifier.width(12.dp))
            Text("Scan Crop (Camera)", color = EmeraldDark, fontWeight = FontWeight.Bold, fontSize = 18.sp)
        }
        
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            // Action 2: Decisions
            Button(
                onClick = onDecision, 
                modifier = Modifier.weight(1f).height(72.dp), 
                colors = ButtonDefaults.buttonColors(containerColor = CardBackground), 
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(Icons.Default.List, contentDescription = "Decisions", tint = Color.White)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("Decision (A vs B)", color = Color.White, fontSize = 12.sp)
                }
            }
            
            // Action 3: Audio Advisory
            Button(
                onClick = onAudio, 
                modifier = Modifier.weight(1f).height(72.dp), 
                colors = ButtonDefaults.buttonColors(containerColor = CardBackground), 
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(Icons.Default.PlayArrow, contentDescription = "Play Audio", tint = Color.White)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("Audio Advisory", color = Color.White, fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
fun RecentDecisionsList() {
    Text("Recent Analyses", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
    Spacer(modifier = Modifier.height(12.dp))
    GlassCard {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column {
                Text("Tomato • Leaf Blight", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                Text("Decision: Act Today", color = MintAccent, fontSize = 14.sp)
            }
            Text("Yesterday", color = Color.White.copy(0.6f), fontSize = 12.sp)
        }
    }
}

@Composable
fun SamsaariBottomNav(
    onHistory: () -> Unit,
    onSettings: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth().background(EmeraldDark.copy(0.95f)).padding(vertical = 12.dp, horizontal = 32.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        NavItem(Icons.Default.Home, "Home", isSelected = true, onClick = {})
        NavItem(Icons.Default.DateRange, "History", isSelected = false, onClick = onHistory)
        NavItem(Icons.Default.Settings, "Settings", isSelected = false, onClick = onSettings)
    }
}

@Composable
fun NavItem(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, isSelected: Boolean, onClick: () -> Unit) {
    val tint = if (isSelected) MintAccent else Color.White.copy(0.5f)
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.clickable { onClick() }.padding(8.dp)
    ) {
        Icon(icon, contentDescription = label, tint = tint, modifier = Modifier.size(28.dp))
        Spacer(modifier = Modifier.height(4.dp))
        Text(label, color = tint, fontSize = 12.sp, fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal)
    }
}

/* ---------------------------------------------------------
   CAMERA / SCAN SCREEN
--------------------------------------------------------- */
private enum class CameraState { Scanning, ImagePreview, Analyzing }

@Composable
fun CropScanScreen(
    onBack: () -> Unit,
    onAnalysisComplete: () -> Unit
) {
    var currentState by remember {
        mutableStateOf(CameraState.Scanning)
    }

    var capturedFile by remember {
        mutableStateOf<File?>(null)
    }

    SamsaariBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(top = 48.dp, bottom = 24.dp)
        ) {

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {

                IconButton(
                    onClick = {
                        if (currentState == CameraState.ImagePreview) {
                            capturedFile = null
                            currentState = CameraState.Scanning
                        } else {
                            onBack()
                        }
                    },
                    modifier = Modifier
                        .clip(CircleShape)
                        .background(CardBackground)
                ) {
                    Icon(
                        Icons.Default.ArrowBack,
                        contentDescription = "Back",
                        tint = Color.White
                    )
                }

                Text(
                    "Crop Scan",
                    color = Color.White,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    "Samsaari",
                    color = MintAccent.copy(0.8f),
                    fontSize = 18.sp,
                    fontFamily = FontFamily.Serif
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Crossfade(
                targetState = currentState,
                label = "Camera State"
            ) { state ->

                when (state) {

                    CameraState.Scanning -> {
                        LiveCameraView(
                            onPhotoCaptured = { file ->
                                capturedFile = file
                                currentState = CameraState.ImagePreview
                            },
                            onGallerySelected = { file ->
                                capturedFile = file
                                currentState = CameraState.ImagePreview
                            }
                        )
                    }

                    CameraState.ImagePreview -> {
                        capturedFile?.let { file ->

                            CapturedPreviewView(
                                file = file,

                                onRetake = {
                                    capturedFile = null
                                    currentState = CameraState.Scanning
                                },

                                onUsePhoto = {
                                    currentState = CameraState.Analyzing
                                }
                            )
                        }
                    }

                    CameraState.Analyzing -> {
                        AnalyzingView(
                            onAnalysisComplete = onAnalysisComplete
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun LiveCameraView(
    onPhotoCaptured: (File) -> Unit,
    onGallerySelected: (File) -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    var imageCapture by remember {
        mutableStateOf<ImageCapture?>(null)
    }

    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED
        )
    }

    val permissionLauncher =
        rememberLauncherForActivityResult(
            ActivityResultContracts.RequestPermission()
        ) { granted ->
            hasCameraPermission = granted
        }

    val galleryLauncher =
        rememberLauncherForActivityResult(
            ActivityResultContracts.GetContent()
        ) { uri: Uri? ->

            uri ?: return@rememberLauncherForActivityResult

            val file = uriToFile(
                context,
                uri
            )

            if (file != null) {
                onGallerySelected(file)
            }
        }

    LaunchedEffect(Unit) {
        if (!hasCameraPermission) {
            permissionLauncher.launch(
                Manifest.permission.CAMERA
            )
        }
    }

    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {

        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 20.dp)
                .clip(RoundedCornerShape(24.dp))
                .background(Color.Black)
        ) {

            if (hasCameraPermission) {

                AndroidView(
                    modifier = Modifier.fillMaxSize(),

                    factory = { ctx ->

                        val previewView =
                            PreviewView(ctx)

                        val cameraProviderFuture =
                            ProcessCameraProvider
                                .getInstance(ctx)

                        cameraProviderFuture.addListener({

                            val cameraProvider =
                                cameraProviderFuture.get()

                            val preview =
                                Preview.Builder()
                                    .build()
                                    .also {
                                        it.surfaceProvider =
                                            previewView.surfaceProvider
                                    }

                            val capture =
                                ImageCapture.Builder()
                                    .setCaptureMode(
                                        ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY
                                    )
                                    .build()

                            imageCapture = capture

                            val selector =
                                CameraSelector.DEFAULT_BACK_CAMERA

                            cameraProvider.unbindAll()

                            cameraProvider.bindToLifecycle(
                                lifecycleOwner,
                                selector,
                                preview,
                                capture
                            )

                        }, ContextCompat.getMainExecutor(ctx))

                        previewView
                    }
                )

                // Existing visual crop frame
                Canvas(
                    modifier = Modifier
                        .fillMaxSize()
                        .graphicsLayer {
                            alpha = 0.99f
                        }
                ) {

                    val cutoutWidth =
                        size.width * 0.8f

                    val cutoutHeight =
                        size.height * 0.6f

                    val topLeftX =
                        (size.width - cutoutWidth) / 2

                    val topLeftY =
                        (size.height - cutoutHeight) / 2

                    drawRoundRect(
                        color = MintAccent.copy(alpha = 0.8f),
                        topLeft = Offset(
                            topLeftX,
                            topLeftY
                        ),
                        size = Size(
                            cutoutWidth,
                            cutoutHeight
                        ),
                        cornerRadius =
                            CornerRadius(40f, 40f),
                        style =
                            androidx.compose.ui.graphics
                                .drawscope.Stroke(
                                    width = 6f
                                )
                    )
                }

                Text(
                    "Position the affected leaf inside the frame",
                    color = Color.White,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .align(Alignment.Center)
                        .padding(horizontal = 40.dp)
                )

                Column(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 32.dp),
                    horizontalAlignment =
                        Alignment.CenterHorizontally
                ) {

                    Row(
                        verticalAlignment =
                            Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Info,
                            contentDescription = null,
                            tint = MintAccent,
                            modifier = Modifier.size(16.dp)
                        )

                        Spacer(
                            Modifier.width(6.dp)
                        )

                        Text(
                            "Keep the leaf well lit",
                            color = Color.White,
                            fontSize = 14.sp
                        )
                    }

                    Text(
                        "Move closer if needed",
                        color = Color.White.copy(0.8f),
                        fontSize = 14.sp
                    )
                }

            } else {

                Column(
                    modifier = Modifier.fillMaxSize(),
                    horizontalAlignment =
                        Alignment.CenterHorizontally,
                    verticalArrangement =
                        Arrangement.Center
                ) {

                    Text(
                        "Camera permission required",
                        color = Color.White,
                        fontSize = 16.sp
                    )

                    Spacer(
                        Modifier.height(12.dp)
                    )

                    Button(
                        onClick = {
                            permissionLauncher.launch(
                                Manifest.permission.CAMERA
                            )
                        },
                        colors =
                            ButtonDefaults.buttonColors(
                                containerColor =
                                    MintAccent
                            )
                    ) {
                        Text(
                            "Allow Camera",
                            color = EmeraldDark
                        )
                    }
                }
            }
        }

        Spacer(
            modifier = Modifier.height(32.dp)
        )

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(
                    horizontal = 40.dp,
                    vertical = 20.dp
                ),
            horizontalArrangement =
                Arrangement.SpaceBetween,
            verticalAlignment =
                Alignment.CenterVertically
        ) {

            IconButton(
                onClick = { },
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(CardBackground)
            ) {
                Icon(
                    Icons.Default.Star,
                    contentDescription = "Flash",
                    tint = Color.White
                )
            }

            Column(
                horizontalAlignment =
                    Alignment.CenterHorizontally
            ) {

                Box(
                    modifier = Modifier
                        .size(80.dp)
                        .clip(CircleShape)
                        .background(
                            Color.White.copy(0.3f)
                        )
                        .clickable {

                            val capture =
                                imageCapture
                                    ?: return@clickable

                            capturePhoto(
                                context,
                                capture,
                                onPhotoCaptured
                            )
                        },
                    contentAlignment =
                        Alignment.Center
                ) {

                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .clip(CircleShape)
                            .background(MintAccent)
                            .border(
                                2.dp,
                                Color.White,
                                CircleShape
                            )
                    )
                }

                Spacer(
                    Modifier.height(8.dp)
                )

                Text(
                    "Capture",
                    color = Color.White,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Column(
                horizontalAlignment =
                    Alignment.CenterHorizontally
            ) {

                IconButton(
                    onClick = {
                        galleryLauncher.launch("image/*")
                    },
                    modifier = Modifier
                        .size(56.dp)
                        .clip(CircleShape)
                        .background(CardBackground)
                ) {
                    Icon(
                        Icons.Default.Menu,
                        contentDescription = "Gallery",
                        tint = Color.White
                    )
                }

                Spacer(
                    Modifier.height(4.dp)
                )

                Text(
                    "Gallery",
                    color = Color.White.copy(0.8f),
                    fontSize = 12.sp
                )
            }
        }
    }
}

fun capturePhoto(
    context: Context,
    imageCapture: ImageCapture,
    onSaved: (File) -> Unit
) {
    val file = File(
        context.cacheDir,
        "samsaari_${System.currentTimeMillis()}.jpg"
    )

    val outputOptions =
        ImageCapture.OutputFileOptions
            .Builder(file)
            .build()

    imageCapture.takePicture(
        outputOptions,
        ContextCompat.getMainExecutor(context),

        object :
            ImageCapture.OnImageSavedCallback {

            override fun onImageSaved(
                outputFileResults:
                ImageCapture.OutputFileResults
            ) {
                onSaved(file)
            }

            override fun onError(
                exception: ImageCaptureException
            ) {
                exception.printStackTrace()
            }
        }
    )
}

fun uriToFile(
    context: Context,
    uri: Uri
): File? {

    return try {

        val file = File(
            context.cacheDir,
            "samsaari_gallery_${System.currentTimeMillis()}.jpg"
        )

        context.contentResolver
            .openInputStream(uri)
            ?.use { input ->

                file.outputStream().use { output ->
                    input.copyTo(output)
                }
            }

        file

    } catch (e: Exception) {
        e.printStackTrace()
        null
    }
}

@Composable
fun CapturedPreviewView(
    file: File,
    onRetake: () -> Unit,
    onUsePhoto: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment =
            Alignment.CenterHorizontally
    ) {

        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 20.dp)
                .clip(RoundedCornerShape(24.dp))
        ) {

            Image(
                bitmap = BitmapFactory
                    .decodeFile(file.absolutePath)
                    .asImageBitmap(),

                contentDescription =
                    "Captured crop",

                modifier = Modifier.fillMaxSize(),

                contentScale =
                    ContentScale.Crop
            )
        }

        Spacer(
            modifier = Modifier.height(32.dp)
        )

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(
                    horizontal = 20.dp,
                    vertical = 20.dp
                ),
            horizontalArrangement =
                Arrangement.spacedBy(16.dp)
        ) {

            Button(
                onClick = onRetake,
                modifier = Modifier
                    .weight(1f)
                    .height(64.dp),
                colors =
                    ButtonDefaults.buttonColors(
                        containerColor =
                            CardBackground
                    ),
                shape =
                    RoundedCornerShape(16.dp),
                border =
                    androidx.compose.foundation
                        .BorderStroke(
                            1.dp,
                            CardBorder
                        )
            ) {
                Text(
                    "Retake",
                    color = Color.White,
                    fontSize = 18.sp
                )
            }

            Button(
                onClick = onUsePhoto,
                modifier = Modifier
                    .weight(1.5f)
                    .height(64.dp),
                colors =
                    ButtonDefaults.buttonColors(
                        containerColor =
                            MintAccent
                    ),
                shape =
                    RoundedCornerShape(16.dp)
            ) {

                Icon(
                    Icons.Default.Check,
                    contentDescription = "Use",
                    tint = EmeraldDark
                )

                Spacer(
                    Modifier.width(8.dp)
                )

                Text(
                    "Use Photo",
                    color = EmeraldDark,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable
fun AnalyzingView(onAnalysisComplete: () -> Unit) {
    LaunchedEffect(Unit) {
        delay(3000)
        onAnalysisComplete()
    }
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Box(modifier = Modifier.fillMaxWidth(0.85f).clip(RoundedCornerShape(24.dp)).background(CardBackground).border(1.dp, CardBorder, RoundedCornerShape(24.dp)).padding(40.dp), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Box(contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(modifier = Modifier.size(80.dp), color = MintAccent, strokeWidth = 6.dp, trackColor = Color.White.copy(0.1f))
                    Icon(Icons.Default.Search, contentDescription = "Analyzing", tint = MintAccent, modifier = Modifier.size(32.dp))
                }
                Spacer(modifier = Modifier.height(32.dp))
                Text("Analyzing your crop...", color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(12.dp))
                Text("Checking crop condition and field risk.", color = Color.White.copy(0.8f), fontSize = 16.sp, textAlign = TextAlign.Center)
            }
        }
    }
}

/* ---------------------------------------------------------
   SHARED COMPONENTS
--------------------------------------------------------- */
@Composable
fun GlassCard(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Box(modifier = modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(CardBackground).border(1.dp, CardBorder, RoundedCornerShape(20.dp)).padding(16.dp)) {
        content()
    }
}

@Composable
fun SplashScreen(onFinished: () -> Unit) {
    LaunchedEffect(Unit) { delay(1500); onFinished() }
    SamsaariBackground {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Samsaari", color = Color.White, fontSize = 58.sp, fontFamily = FontFamily.Serif)
        }
    }
}

@Composable
fun PlaceholderScreen(title: String, onClick: () -> Unit) {
    SamsaariBackground {
        Column(modifier = Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Text(title, color = Color.White, fontSize = 32.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(60.dp))
            Button(onClick = onClick, colors = ButtonDefaults.buttonColors(containerColor = MintAccent), modifier = Modifier.size(200.dp, 60.dp)) {
                Text("Back", color = EmeraldDark, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}