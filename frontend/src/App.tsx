import { AttendanceTable } from './components/AttendanceTable';
import { DeviceList } from './components/DeviceList';
import './index.css';

function App() {
    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 py-6">
                    <h1 className="text-3xl font-bold text-gray-900">ZIAS Admin Dashboard</h1>
                    <p className="text-gray-600 mt-1">Zero Interaction Attendance System</p>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-8">
                <div className="space-y-8">
                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="text-sm text-gray-600">Total Students</div>
                            <div className="text-3xl font-bold text-gray-900 mt-2">2,450</div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="text-sm text-gray-600">Present Today</div>
                            <div className="text-3xl font-bold text-green-600 mt-2">2,102</div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="text-sm text-gray-600">Absent Today</div>
                            <div className="text-3xl font-bold text-red-600 mt-2">348</div>
                        </div>
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="text-sm text-gray-600">Active Devices</div>
                            <div className="text-3xl font-bold text-blue-600 mt-2">45</div>
                        </div>
                    </div>

                    {/* Devices */}
                    <DeviceList />

                    {/* Attendance Table */}
                    <AttendanceTable />
                </div>
            </main>
        </div>
    );
}

export default App;
