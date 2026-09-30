package com.krishitwin.samsaari

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle

import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

import android.location.Location
import android.location.LocationManager
import android.os.Looper
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.resume
import android.util.Log
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
import java.util.Calendar

private const val API_URL =
    "https://samsaari.onrender.com/api/v1/simulate"

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
    Splash, Dashboard, Camera, Decision, AudioPlay
}

@Composable
fun SamsaariApp() {
    var screen by remember { mutableStateOf(Screen.Splash) }
    var analysisResult by remember { mutableStateOf<JSONObject?>(null) }

    Crossfade(targetState = screen, label = "AppRouter") { currentScreen ->
        when (currentScreen) {
            Screen.Splash -> SplashScreen(
                onFinished = { screen = Screen.Dashboard }
            )

            Screen.Dashboard -> DashboardScreen(
                analysisResult = analysisResult,
                onScanCrop = { screen = Screen.Camera },
                onDecision = {
                    if (analysisResult != null) screen = Screen.Decision
                },
                onAudio = {
                    if (analysisResult != null) screen = Screen.AudioPlay
                }
            )

            Screen.Camera -> {
                CropScanScreen(
                    onBack = {
                        screen = Screen.Dashboard
                    },
                    onAnalysisComplete = { result ->
                        analysisResult = result
                        screen = Screen.Decision
                    }
                )
            }

            Screen.Decision -> {
                analysisResult?.let { result ->
                    DecisionScreen(
                        result = result,
                        onBack = {
                            screen = Screen.Dashboard
                        },
                        onAudio = {
                            screen = Screen.AudioPlay
                        }
                    )
                } ?: run {
                    PlaceholderScreen(
                        title = "No Decision Available",
                        onClick = {
                            screen = Screen.Dashboard
                        }
                    )
                }
            }

            Screen.AudioPlay -> {
                analysisResult?.let { result ->
                    AudioAdvisoryScreen(
                        result = result,
                        onBack = { screen = Screen.Decision }
                    )
                } ?: PlaceholderScreen(
                    "Audio Advisory",
                    onClick = { screen = Screen.Dashboard }
                )
            }
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
                    colors = listOf(
                        Color.Transparent,
                        Color(0x22FFFFFF),
                        Color(0x11FFFFFF),
                        Color.Transparent
                    ),
                    start = Offset(0f, size.height * 0.40f),
                    end = Offset(size.width * 0.80f, size.height)
                )
            )
        }

        content()
    }
}

/* ---------------------------------------------------------
   DYNAMIC DASHBOARD
--------------------------------------------------------- */
@Composable
fun DashboardScreen(
    analysisResult: JSONObject?,
    onScanCrop: () -> Unit,
    onDecision: () -> Unit,
    onAudio: () -> Unit
) {
    val context = LocalContext.current

    var hasLocationPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED ||
                ContextCompat.checkSelfPermission(
                    context,
                    Manifest.permission.ACCESS_COARSE_LOCATION
                ) == PackageManager.PERMISSION_GRANTED
        )
    }

    var location by remember { mutableStateOf<Location?>(null) }

    val locationPermissionLauncher =
        rememberLauncherForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { permissions ->
            hasLocationPermission =
                permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
                    permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        }

    LaunchedEffect(Unit) {
        if (!hasLocationPermission) {
            locationPermissionLauncher.launch(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
                )
            )
        }
    }

    LaunchedEffect(hasLocationPermission) {
        if (hasLocationPermission) {
            location = withContext(Dispatchers.IO) {
                getCurrentLocation(context)
            }
        }
    }

    val greeting = remember {
        when (Calendar.getInstance().get(Calendar.HOUR_OF_DAY)) {
            in 5..11 -> "Good morning"
            in 12..16 -> "Good afternoon"
            in 17..20 -> "Good evening"
            else -> "Good night"
        }
    }

    val disease = analysisResult?.optString("disease", "").orEmpty()
    val confidence = analysisResult?.optDouble("disease_confidence", -1.0) ?: -1.0
    val uncertain = analysisResult?.optBoolean("disease_uncertain", false) ?: false
    val action = analysisResult?.optString("recommended_action", "").orEmpty()
    val risk = analysisResult?.optString("risk_factor", "").orEmpty()
    val language = analysisResult?.optString("resolved_language", "").orEmpty()

    SamsaariBackground {
        Column(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier
                    .weight(1f)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(modifier = Modifier.height(56.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            "Samsaari",
                            color = Color.White,
                            fontSize = 32.sp,
                            fontFamily = FontFamily.Serif
                        )

                        Text(
                            greeting,
                            color = Color.White.copy(alpha = 0.8f),
                            fontSize = 16.sp
                        )
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))

                CurrentFieldCard(location = location)

                Spacer(modifier = Modifier.height(16.dp))

                if (analysisResult == null) {
                    GlassCard {
                        Column {
                            Text(
                                "No analysis yet",
                                color = Color.White,
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Bold
                            )

                            Spacer(modifier = Modifier.height(8.dp))

                            Text(
                                "Scan a rice leaf to load live disease, field-risk and decision data.",
                                color = Color.White.copy(alpha = 0.75f),
                                fontSize = 14.sp,
                                lineHeight = 20.sp
                            )
                        }
                    }
                } else {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Box(modifier = Modifier.weight(1f)) {
                            CropHealthCard(
                                disease = disease,
                                confidence = confidence,
                                uncertain = uncertain
                            )
                        }

                        Box(modifier = Modifier.weight(1f)) {
                            RiskCard(
                                action = action,
                                risk = risk
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    GlassCard {
                        Column {
                            Text(
                                "Latest Analysis",
                                color = Color.White.copy(alpha = 0.75f),
                                fontSize = 14.sp
                            )

                            Spacer(modifier = Modifier.height(6.dp))

                            Text(
                                disease.ifBlank { "Analysis complete" },
                                color = Color.White,
                                fontSize = 22.sp,
                                fontWeight = FontWeight.Bold
                            )

                            if (confidence >= 0.0) {
                                Spacer(modifier = Modifier.height(6.dp))

                                Text(
                                    "Confidence: ${"%.1f".format(confidence * 100)}%",
                                    color = if (uncertain) AlertCoral else MintAccent,
                                    fontSize = 14.sp
                                )
                            }

                            if (language.isNotBlank()) {
                                Spacer(modifier = Modifier.height(6.dp))

                                Text(
                                    "Advisory language: ${language.uppercase()}",
                                    color = Color.White.copy(alpha = 0.7f),
                                    fontSize = 13.sp
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))

                Text(
                    "Actions",
                    color = Color.White,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(modifier = Modifier.height(12.dp))

                Button(
                    onClick = onScanCrop,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(72.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MintAccent
                    ),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Icon(
                        Icons.Default.Search,
                        contentDescription = "Scan",
                        tint = EmeraldDark
                    )

                    Spacer(modifier = Modifier.width(12.dp))

                    Text(
                        "Scan Crop",
                        color = EmeraldDark,
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp
                    )
                }

                if (analysisResult != null) {
                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Button(
                            onClick = onDecision,
                            modifier = Modifier
                                .weight(1f)
                                .height(64.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = CardBackground
                            ),
                            shape = RoundedCornerShape(16.dp)
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Icon(
                                    Icons.Default.List,
                                    contentDescription = "Decision",
                                    tint = Color.White
                                )

                                Text(
                                    "Decision",
                                    color = Color.White,
                                    fontSize = 12.sp
                                )
                            }
                        }

                        Button(
                            onClick = onAudio,
                            modifier = Modifier
                                .weight(1f)
                                .height(64.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = CardBackground
                            ),
                            shape = RoundedCornerShape(16.dp)
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Icon(
                                    Icons.Default.PlayArrow,
                                    contentDescription = "Audio",
                                    tint = Color.White
                                )

                                Text(
                                    "Audio",
                                    color = Color.White,
                                    fontSize = 12.sp
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}

@Composable
fun CurrentFieldCard(location: Location?) {
    GlassCard {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "Current Field",
                    color = Color.White,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(modifier = Modifier.height(8.dp))

                if (location != null) {
                    Text(
                        "GPS location available",
                        color = MintAccent,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        "%.6f, %.6f".format(
                            location.latitude,
                            location.longitude
                        ),
                        color = Color.White.copy(alpha = 0.75f),
                        fontSize = 13.sp
                    )
                } else {
                    Text(
                        "Waiting for device location...",
                        color = Color.White.copy(alpha = 0.75f),
                        fontSize = 14.sp
                    )
                }
            }

            Icon(
                Icons.Default.LocationOn,
                contentDescription = "Current location",
                tint = MintAccent,
                modifier = Modifier.size(32.dp)
            )
        }
    }
}

@Composable
fun CropHealthCard(
    disease: String,
    confidence: Double,
    uncertain: Boolean
) {
    GlassCard(modifier = Modifier.fillMaxHeight()) {
        Column {
            Text(
                "Crop Analysis",
                color = Color.White.copy(0.8f),
                fontSize = 14.sp
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                disease.ifBlank { "Unknown" },
                color = if (uncertain) AlertCoral else Color.White,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )

            if (confidence >= 0.0) {
                Spacer(modifier = Modifier.height(14.dp))

                CircularProgressIndicator(
                    progress = {
                        confidence.coerceIn(0.0, 1.0).toFloat()
                    },
                    modifier = Modifier.size(32.dp),
                    color = if (uncertain) AlertCoral else MintAccent,
                    trackColor = Color.White.copy(0.2f),
                    strokeWidth = 4.dp
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    "${"%.1f".format(confidence * 100)}% confidence",
                    color = Color.White.copy(0.7f),
                    fontSize = 12.sp
                )
            }
        }
    }
}

@Composable
fun RiskCard(
    action: String,
    risk: String
) {
    GlassCard(modifier = Modifier.fillMaxHeight()) {
        Column {
            Text(
                "Field Risk",
                color = Color.White.copy(0.8f),
                fontSize = 14.sp
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                action.ifBlank { "WAIT" },
                color = if (action.equals("WAIT", ignoreCase = true)) {
                    AlertCoral
                } else {
                    MintAccent
                },
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                risk.ifBlank { "Risk data returned by the analysis engine." },
                color = Color.White.copy(alpha = 0.75f),
                fontSize = 12.sp,
                lineHeight = 17.sp,
                maxLines = 6
            )
        }
    }
}

/* ---------------------------------------------------------
   CAMERA / SCAN SCREEN
--------------------------------------------------------- */
private enum class CameraState { Scanning, ImagePreview, Analyzing }

@Composable
fun CropScanScreen(
    onBack: () -> Unit,
    onAnalysisComplete: (JSONObject) -> Unit
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
                        capturedFile?.let { file ->
                            AnalyzingView(
                                imageFile = file,

                                onAnalysisComplete = { result ->
                                    println("Samsaari API response: $result")

                                    onAnalysisComplete(result)
                                },

                                onError = { error ->
                                    println("Samsaari API error: $error")

                                    capturedFile = null
                                    currentState = CameraState.Scanning
                                }
                            )
                        }
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
suspend fun getCurrentLocation(context: Context): Location? {
    val fineGranted =
        ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

    val coarseGranted =
        ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED

    if (!fineGranted && !coarseGranted) {
        Log.e("Samsaari", "Location permission not granted")
        return null
    }

    val locationManager =
        context.getSystemService(Context.LOCATION_SERVICE) as LocationManager

    if (!locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
        Log.e("Samsaari", "GPS provider is disabled")
        return null
    }

    /*
     * GPS is intentionally the only location source used for the farm
     * coordinates. Do not substitute network/provider coordinates.
     */
    try {
        val gpsLocation =
            locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)

        if (gpsLocation != null) {
            Log.d(
                "Samsaari",
                "Using last GPS location = ${gpsLocation.latitude}, ${gpsLocation.longitude}"
            )
            return gpsLocation
        }
    } catch (e: SecurityException) {
        Log.e("Samsaari", "Location permission error", e)
        return null
    }

    /*
     * No cached GPS location: request a fresh GPS fix.
     * A timeout prevents the analysis screen from waiting forever.
     */
    return withTimeoutOrNull(15_000L) {
        suspendCancellableCoroutine { continuation ->

            val listener = object : android.location.LocationListener {

                override fun onLocationChanged(location: Location) {
                    Log.d(
                        "Samsaari",
                        "Fresh GPS location = ${location.latitude}, ${location.longitude}"
                    )

                    if (continuation.isActive) {
                        continuation.resume(location)
                    }

                    locationManager.removeUpdates(this)
                }

                override fun onProviderDisabled(provider: String) {}

                override fun onProviderEnabled(provider: String) {}

                @Suppress("DEPRECATION")
                override fun onStatusChanged(
                    provider: String?,
                    status: Int,
                    extras: android.os.Bundle?
                ) {}
            }

            try {
                locationManager.requestLocationUpdates(
                    LocationManager.GPS_PROVIDER,
                    1000L,
                    1f,
                    listener,
                    Looper.getMainLooper()
                )

                continuation.invokeOnCancellation {
                    locationManager.removeUpdates(listener)
                }

            } catch (e: SecurityException) {
                Log.e("Samsaari", "Failed to request GPS", e)

                locationManager.removeUpdates(listener)

                if (continuation.isActive) {
                    continuation.resume(null)
                }
            }
        }
    }
}

@Composable
fun AnalyzingView(
    imageFile: File,
    onAnalysisComplete: (JSONObject) -> Unit,
    onError: (String) -> Unit
) {
    val context = LocalContext.current

    var hasLocationPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_COARSE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED
        )
    }

    var permissionRequested by remember {
        mutableStateOf(false)
    }

    val locationPermissionLauncher =
        rememberLauncherForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { permissions ->

            hasLocationPermission =
                permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
                permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        }

    // Ask for location permission before analysis.
    LaunchedEffect(Unit) {
        if (!hasLocationPermission && !permissionRequested) {
            permissionRequested = true

            locationPermissionLauncher.launch(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
                )
            )
        }
    }

    LaunchedEffect(imageFile, hasLocationPermission) {

        if (!hasLocationPermission) {
            return@LaunchedEffect
        }

        try {
            Log.d("Samsaari", "Starting analysis")

            val result = withContext(Dispatchers.IO) {

                Log.d("Samsaari", "Getting current location")

                val location = getCurrentLocation(context)

                if (location == null) {
                    throw Exception(
                        "Unable to get your current location. Please enable GPS/location services."
                    )
                }

                val latitude = location.latitude
                val longitude = location.longitude

                Log.d("Samsaari", "GPS latitude = $latitude")
                Log.d("Samsaari", "GPS longitude = $longitude")

                Log.d("Samsaari", "Reading image")

                val imageBytes = imageFile.readBytes()

                Log.d("Samsaari", "Image size = ${imageBytes.size} bytes")

                val imageBase64 = Base64.encodeToString(
                    imageBytes,
                    Base64.NO_WRAP
                )

                Log.d("Samsaari", "Base64 created")

                val payload = JSONObject().apply {

                    put(
                        "engine",
                        "samsaari-v2"
                    )

                    put(
                        "timestamp",
                        java.time.Instant.now().toString()
                    )

                    put(
                        "farm_profile",
                        JSONObject().apply {

                            put(
                                "coordinates",
                                JSONObject().apply {
                                    put(
                                        "latitude",
                                        latitude
                                    )

                                    put(
                                        "longitude",
                                        longitude
                                    )
                                }
                            )

                            put(
                                "crop",
                                "rice"
                            )
                        }
                    )

                    put(
                        "geospatial_telemetry",
                        JSONObject()
                    )

                    put(
                        "meteorological_risk",
                        JSONObject()
                    )

                    put(
                        "market_telemetry",
                        JSONObject()
                    )

                    put(
                        "financial_inputs",
                        JSONObject()
                    )

                    put(
                        "image_base64",
                        imageBase64
                    )
                }

                Log.d("Samsaari", "Payload coordinates = $latitude, $longitude")

                val requestBody =
                    payload
                        .toString()
                        .toRequestBody(
                            "application/json".toMediaType()
                        )

                val request =
                    Request.Builder()
                        .url(API_URL)
                        .post(requestBody)
                        .build()

                Log.d("Samsaari", "Sending request")

                val client =
                    OkHttpClient.Builder()
                        .connectTimeout(
                            60,
                            java.util.concurrent.TimeUnit.SECONDS
                        )
                        .writeTimeout(
                            60,
                            java.util.concurrent.TimeUnit.SECONDS
                        )
                        .readTimeout(
                            120,
                            java.util.concurrent.TimeUnit.SECONDS
                        )
                        .callTimeout(
                            120,
                            java.util.concurrent.TimeUnit.SECONDS
                        )
                        .build()

                client.newCall(request).execute().use { response ->

                    Log.d("Samsaari", "HTTP ${response.code}")

                    val responseBody =
                        response.body?.string()
                            ?: throw Exception(
                                "Empty server response"
                            )

                    Log.d("Samsaari", "Response received")

                    Log.d("Samsaari", "Response body = $responseBody")

                    if (!response.isSuccessful) {
                        throw Exception(
                            "Server error ${response.code}: $responseBody"
                        )
                    }

                    val result = JSONObject(responseBody)

                    Log.d(
                        "Samsaari",
                        "Resolved language = ${result.optString("resolved_language", "N/A")}"
                    )
                    Log.d(
                        "Samsaari",
                        "Disease = ${result.optString("disease", "N/A")}"
                    )
                    Log.d(
                        "Samsaari",
                        "Disease confidence = ${result.optDouble("disease_confidence", 0.0)}"
                    )

                    result
                }
            }

            Log.d("Samsaari", "Analysis complete")

            onAnalysisComplete(result)

        } catch (e: Exception) {

            Log.e("Samsaari", "ERROR ${e.javaClass.simpleName}: ${e.message}", e)

            e.printStackTrace()

            onError(
                e.message ?: "Analysis failed"
            )
        }
    }

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {

        Box(
            modifier = Modifier
                .fillMaxWidth(0.85f)
                .clip(RoundedCornerShape(24.dp))
                .background(CardBackground)
                .border(
                    1.dp,
                    CardBorder,
                    RoundedCornerShape(24.dp)
                )
                .padding(40.dp),
            contentAlignment = Alignment.Center
        ) {

            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {

                Box(
                    contentAlignment = Alignment.Center
                ) {

                    CircularProgressIndicator(
                        modifier = Modifier.size(80.dp),
                        color = MintAccent,
                        strokeWidth = 6.dp,
                        trackColor = Color.White.copy(0.1f)
                    )

                    Icon(
                        Icons.Default.Search,
                        contentDescription = "Analyzing",
                        tint = MintAccent,
                        modifier = Modifier.size(32.dp)
                    )
                }

                Spacer(
                    modifier = Modifier.height(32.dp)
                )

                Text(
                    "Analyzing your crop...",
                    color = Color.White,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(
                    modifier = Modifier.height(12.dp)
                )

                Text(
                    if (hasLocationPermission)
                        "Getting your location and checking field risk."
                    else
                        "Location permission is required for field analysis.",
                    color = Color.White.copy(0.8f),
                    fontSize = 16.sp,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}
@Composable
fun DecisionScreen(
    result: JSONObject,
    onBack: () -> Unit,
    onAudio: () -> Unit
) {
    val recommendedAction = result.optString("recommended_action", "WAIT")
    val disease = result.optString("disease", "Unknown")
    val confidence = result.optDouble("disease_confidence", 0.0)
    val uncertain = result.optBoolean("disease_uncertain", false)
    val scenarioA = result.optString("scenario_a_roi_inr", "N/A")
    val scenarioB = result.optString("scenario_b_roi_inr", "N/A")
    val risk = result.optString("risk_factor", "N/A")
    val translatedText = result.optString(
        "translated_text",
        result.optString("voice_script_2_sentences", "")
    )

    SamsaariBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 48.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                IconButton(
                    onClick = onBack,
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
                    "Decision",
                    color = Color.White,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    "Samsaari",
                    color = MintAccent.copy(alpha = 0.8f),
                    fontSize = 18.sp,
                    fontFamily = FontFamily.Serif
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            GlassCard {
                Column {
                    Text(
                        "Crop Analysis",
                        color = Color.White.copy(alpha = 0.75f),
                        fontSize = 14.sp
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        disease,
                        color = Color.White,
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "Confidence: ${"%.1f".format(confidence * 100)}%",
                        color = if (uncertain) AlertCoral else MintAccent,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Medium
                    )
                    if (uncertain) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "The model is below the 70% confidence threshold. The backend safety rule recommends WAIT.",
                            color = AlertCoral,
                            fontSize = 14.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            GlassCard {
                Column {
                    Text(
                        "Recommended Action",
                        color = Color.White.copy(alpha = 0.75f),
                        fontSize = 14.sp
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        recommendedAction,
                        color = if (recommendedAction.equals("WAIT", ignoreCase = true))
                            AlertCoral else MintAccent,
                        fontSize = 30.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                GlassCard(modifier = Modifier.weight(1f)) {
                    Column {
                        Text(
                            "Scenario A",
                            color = Color.White.copy(alpha = 0.7f),
                            fontSize = 13.sp
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            "Act Today",
                            color = Color.White,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            scenarioA,
                            color = MintAccent,
                            fontSize = 15.sp
                        )
                    }
                }

                GlassCard(modifier = Modifier.weight(1f)) {
                    Column {
                        Text(
                            "Scenario B",
                            color = Color.White.copy(alpha = 0.7f),
                            fontSize = 13.sp
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            "Wait",
                            color = Color.White,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            scenarioB,
                            color = MintAccent,
                            fontSize = 15.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            GlassCard {
                Column {
                    Text(
                        "Risk Factor",
                        color = Color.White.copy(alpha = 0.7f),
                        fontSize = 14.sp
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        risk,
                        color = Color.White,
                        fontSize = 16.sp
                    )
                }
            }

            if (translatedText.isNotBlank()) {
                Spacer(modifier = Modifier.height(16.dp))

                GlassCard {
                    Column {
                        Text(
                            "Advisory",
                            color = Color.White.copy(alpha = 0.7f),
                            fontSize = 14.sp
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            translatedText,
                            color = Color.White,
                            fontSize = 16.sp,
                            lineHeight = 24.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Button(
                onClick = onAudio,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(62.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MintAccent
                ),
                shape = RoundedCornerShape(16.dp)
            ) {
                Icon(
                    Icons.Default.PlayArrow,
                    contentDescription = "Play audio",
                    tint = EmeraldDark
                )
                Spacer(modifier = Modifier.width(10.dp))
                Text(
                    "Play Audio Advisory",
                    color = EmeraldDark,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
fun AudioAdvisoryScreen(
    result: JSONObject,
    onBack: () -> Unit
) {
    val audioBase64 = result.optString("audio_base64", "")
    val advisory = result.optString(
        "translated_text",
        result.optString("voice_script_2_sentences", "")
    )
    val context = LocalContext.current

    var isPlaying by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    DisposableEffect(audioBase64) {
        var player: android.media.MediaPlayer? = null

        if (audioBase64.isNotBlank()) {
            try {
                val audioBytes = Base64.decode(audioBase64, Base64.DEFAULT)
                val audioFile = File(
                    context.cacheDir,
                    "samsaari_advisory_${System.currentTimeMillis()}.mp3"
                )
                audioFile.writeBytes(audioBytes)

                player = android.media.MediaPlayer().apply {
                    setDataSource(audioFile.absolutePath)
                    setOnPreparedListener {
                        isPlaying = true
                        it.start()
                    }
                    setOnCompletionListener {
                        isPlaying = false
                    }
                    setOnErrorListener { _, _, _ ->
                        isPlaying = false
                        error = "Unable to play audio"
                        true
                    }
                    prepareAsync()
                }
            } catch (e: Exception) {
                error = e.message ?: "Unable to prepare audio"
            }
        } else {
            error = "No audio advisory was returned by the server"
        }

        onDispose {
            player?.release()
        }
    }

    SamsaariBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 48.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = onBack,
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

                Spacer(modifier = Modifier.width(16.dp))

                Text(
                    "Audio Advisory",
                    color = Color.White,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(28.dp))

            GlassCard {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        Icons.Default.PlayArrow,
                        contentDescription = "Audio",
                        tint = MintAccent,
                        modifier = Modifier.size(64.dp)
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    Text(
                        if (isPlaying) "Playing advisory..." else "Audio advisory",
                        color = Color.White,
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Center
                    )

                    if (advisory.isNotBlank()) {
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            advisory,
                            color = Color.White.copy(alpha = 0.8f),
                            fontSize = 16.sp,
                            lineHeight = 24.sp,
                            textAlign = TextAlign.Center
                        )
                    }

                    error?.let {
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            it,
                            color = AlertCoral,
                            fontSize = 14.sp,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Button(
                onClick = {
                    // Playback starts automatically when the MediaPlayer is prepared.
                },
                enabled = false,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(60.dp),
                colors = ButtonDefaults.buttonColors(
                    disabledContainerColor = MintAccent.copy(alpha = 0.45f)
                ),
                shape = RoundedCornerShape(16.dp)
            ) {
                Icon(
                    if (isPlaying) Icons.Default.PlayArrow else Icons.Default.PlayArrow,
                    contentDescription = null,
                    tint = EmeraldDark
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    if (isPlaying) "Playing" else "Preparing Audio",
                    color = EmeraldDark,
                    fontWeight = FontWeight.Bold
                )
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