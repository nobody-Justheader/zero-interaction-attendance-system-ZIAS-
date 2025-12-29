import { useState, useEffect } from 'react';
import { attendanceAPI } from '../services/api';

interface AttendanceRecord {
    id: string;
    student_id: string;
    student_name: string;
    room: string;
    entry_time: string;
    exit_time: string | null;
    status: string;
}

export const AttendanceTable = () => {
    const [records, setRecords] = useState<AttendanceRecord[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchRecords();
        const interval = setInterval(fetchRecords, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const fetchRecords = async () => {
        try {
            const response = await attendanceAPI.getRecords({ limit: 50 });
            setRecords(response.data.records || []);
        } catch (error) {
            console.error('Failed to fetch attendance records:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="bg-white rounded-lg shadow p-6">Loading...</div>;
    }

    return (
        <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Recent Attendance</h2>
            </div>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Student
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Room
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Entry Time
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Exit Time
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {records.map((record: AttendanceRecord) => (
                            <tr key={record.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm font-medium text-gray-900">{record.student_name}</div>
                                    <div className="text-sm text-gray-500">{record.student_id}</div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {record.room}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {new Date(record.entry_time).toLocaleString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {record.exit_time ? new Date(record.exit_time).toLocaleString() : '-'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span
                                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${record.status === 'present'
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-gray-100 text-gray-800'
                                            }`}
                                    >
                                        {record.status}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {records.length === 0 && (
                    <div className="text-center py-8 text-gray-500">No attendance records found</div>
                )}
            </div>
        </div>
    );
};
