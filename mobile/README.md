# ZIAS Mobile App (Flutter)

## Setup

```bash
flutter create zias_mobile
cd zias_mobile
```

## Dependencies

Add to `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_beacon: ^0.5.1  # BLE beacon scanning
  geolocator: ^10.1.0     # Geofencing
  permission_handler: ^11.1.0  # Permissions
  http: ^1.1.2            # API calls
  mqtt_client: ^10.0.0    # MQTT for real-time
  shared_preferences: ^2.2.2  # Local storage
```

## Key Features

1. **Background BLE Scanning**
2. **Geofencing Validation**
3. **Push Notifications**
4. **Offline Queue**
5. **Attendance History**

## Implementation Status

Phase 2: Foundation created  
Phase 3: Full mobile app development

See `mobile/README.md` for implementation guide.
