package ca.jetsphere.alignsilder.devices;

import android.content.Context;
import android.hardware.Camera;
import android.util.AttributeSet;

import org.opencv.android.JavaCameraView;

/**
 *
 */
public class MyJavaCameraView extends JavaCameraView
{
    private static String TAG = "MyJavaCameraView";

    /**
     *
     */
    public MyJavaCameraView(Context context, int cameraId) {
        super(context, cameraId);
    }

    /**
     *
     */
    public MyJavaCameraView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    /**
     *
     */
    public void torchOff() {
        if (mCamera == null) return;

        Camera.Parameters params = mCamera.getParameters();
        params.setFlashMode(params.FLASH_MODE_OFF);
        mCamera.setParameters(params);
        mCamera.startPreview();
    }

    /**
     *
     */
    public void torchOn() {
        if (mCamera == null) return;

        Camera.Parameters params = mCamera.getParameters();
        params.setFlashMode(params.FLASH_MODE_TORCH);
        mCamera.setParameters(params);
        mCamera.startPreview();
    }
}
