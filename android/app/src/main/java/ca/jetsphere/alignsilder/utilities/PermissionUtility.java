package ca.jetsphere.alignsilder.utilities;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.support.v4.app.ActivityCompat;

import static android.content.Context.MODE_PRIVATE;

public class PermissionUtility
{
    final static String PREFS_FILE_NAME = "RobotCarPermissions";

    /**
     *
     */
    public static void checkPermission(Context context, String permission, PermissionAskListener listener){
        /*
         * If permission is not granted
         * */
        if (shouldAskPermission(context, permission)){
            /*
             * If permission denied previously
             * */
            if (ActivityCompat.shouldShowRequestPermissionRationale((Activity) context, permission)) {
                listener.onPermissionPreviouslyDenied();
            } else {
                /*
                 * Permission denied or first time requested
                 * */
                if (isFirstTimeAskingPermission(context, permission)) {
                    firstTimeAskingPermission(context, permission, false);
                    listener.onNeedPermission();
                } else {
                    /*
                     * Handle the feature without permission or ask user to manually allow permission
                     * */
                    listener.onPermissionDisabled();
                }
            }
        } else {
            listener.onPermissionGranted();
        }
    }

    /**
     *
     */
    public static void firstTimeAskingPermission(Context context, String permission, boolean isFirstTime){
        SharedPreferences sharedPreference = context.getSharedPreferences(PREFS_FILE_NAME, MODE_PRIVATE);
        sharedPreference.edit().putBoolean(permission, isFirstTime).apply();
    }

    /**
     *
     */
    public static boolean isFirstTimeAskingPermission(Context context, String permission){
        return context.getSharedPreferences(PREFS_FILE_NAME, MODE_PRIVATE).getBoolean(permission, true);
    }

    /**
     *
     */
    public static boolean shouldAskPermission() {
        return (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M);
    }

    /**
     *
     */
    private static boolean shouldAskPermission(Context context, String permission){
        if (shouldAskPermission()) {
            int permissionResult = ActivityCompat.checkSelfPermission(context, permission);
            if (permissionResult != PackageManager.PERMISSION_GRANTED) {
                return true;
            }
        }
        return false;
    }

    /**
     *
     */
    public interface PermissionAskListener {
        void onNeedPermission(); // Callback to ask permission
        void onPermissionPreviouslyDenied(); // Callback on permission denied
        void onPermissionDisabled(); // Callback on permission "Never show again" checked and denied
        void onPermissionGranted(); // Callback on permission granted
    }
}
