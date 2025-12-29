import { useState, useEffect } from 'react';
import { devicesAPI } from '../services/api';

interface Device {
    device_id: string;
    room: string;
    status: string;
    has_rfid: boolean;
    has_pir: boolean;
    has_camera: boolean;
    has_ble: boolean;
    ip: string;
    last_seen: string | null;
}

export const DeviceList = () => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDevices();
        const interval = setInterval(fetchDevices, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, []);

    const fetchDevices = async () => {
        try {
            const response = await devicesAPI.list();
            setDevices(response.data.devices || []);
        } catch (error) {
            console.error('Failed to fetch devices:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active':
                return 'bg-green-100 text-green-800';
            case 'inactive':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="bg-white rounded-lg shadow p-6">Loading devices...</div>;
    }

    return (
        <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Active Devices</h2>
            </div>
            <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {devices.map((device: Device) => (
                        <div
                            key={device.device_id}
                            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
                        >
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <h3 className="font-medium text-gray-900">{device.device_id}</h3>
                                    <p className="text-sm text-gray-500">{device.room}</p>
                                </div>
                                <span
                                    className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                                        device.status
                                    )}`}
                                >
                                    {device.status}
                                </span>
                            </div>

                            <div className="space-y-2">
                                <div className="flex flex-wrap gap-1">
                                    {device.has_rfid && (
                                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                            RFID
                                        </span>
                                    )}
                                    {device.has_pir && (
                                        <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">
                                            PIR
                                        </span>
                                    )}
                                    {device.has_camera && (
                                        <span className="bg-indigo-100 text-indigo-800 text-xs px-2 py-1 rounded">
                                            Camera
                                        </span>
                                    )}
                                    {device.has_ble && (
                                        <span className="bg-cyan-100 text-cyan-800 text-xs px-2 py-1 rounded">
                                            BLE
                                        </span>
                                    )}
                                </div>
                                <div className="text-xs text-gray-500">
                                    <div>IP: {device.ip || 'N/A'}</div>
                                    <div>
                                        Last seen:{' '}
                                        {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
                {devices.length === 0 && (
                    <div className="text-center py-8 text-gray-500">No devices found</div>
                )}
            </div>
        </div>
    );
};
