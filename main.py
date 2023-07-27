from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QTimer, Qt
import sys
import psutil
import os


class ProcessTable(QTableWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setGeometry(300, 300, 800, 800)
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(
            ["ProcessName", "p_id", "CPUUsage", "CPUPercentage", "MEMUsage (MB)", "IOUtilization", "IOBound"])
        self.prev_io_counters = {}
        self.prev_cpu_times = {}
        self.update()

        self.timer = QTimer()
        self.timer.setInterval(10000)  # 10 seconds
        self.timer.timeout.connect(self.update)
        self.timer.start()

        self.setSortingEnabled(True)  # Enable sorting

    def update(self):
        self.setSortingEnabled(False)  # Disable sorting during update

        self.setRowCount(0)

        total_cpu_time = psutil.cpu_times().user  # Get total CPU time

        process_data = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'io_counters', 'cpu_times']):
            if proc.info['io_counters'] is not None:
                io_counters_current = proc.info['io_counters'].read_bytes + proc.info['io_counters'].write_bytes
                io_counters_prev = self.prev_io_counters.get(proc.info['pid'], io_counters_current)
                self.prev_io_counters[proc.info['pid']] = io_counters_current

                io_utilization = io_counters_current - io_counters_prev  # Difference in total IO bytes
            else:
                io_utilization = 0

            if proc.info['cpu_times'] is not None:
                cpu_time_current = proc.info['cpu_times'].user
                cpu_time_prev = self.prev_cpu_times.get(proc.info['pid'], cpu_time_current)
                self.prev_cpu_times[proc.info['pid']] = cpu_time_current

                cpu_usage = cpu_time_current - cpu_time_prev
                cpu_percentage = (cpu_usage / total_cpu_time) * 10000 if total_cpu_time > 0 else 0
            else:
                cpu_usage = 0
                cpu_percentage = 0

            if cpu_usage > io_utilization:
                process_type = "CPU-bound"
            else:
                process_type = "I/O-bound"

            # Memory usage in MB
            mem_usage_MB = round(proc.info['memory_info'].rss / (1024 ** 2), 3)

            process_data.append(
                (proc.info['name'], proc.info['pid'], cpu_usage, cpu_percentage, mem_usage_MB, io_utilization,
                 process_type)
            )

        # Sort the process data by the "MEMUsage (MB)" column
        process_data.sort(key=lambda x: x[4])

        self.setRowCount(len(process_data))

        for row, process in enumerate(process_data):
            self.setItem(row, 0, QTableWidgetItem(process[0]))

            item_pid = QTableWidgetItem()
            item_pid.setData(Qt.DisplayRole, process[1])
            self.setItem(row, 1, item_pid)

            item_cpu = QTableWidgetItem()
            item_cpu.setData(Qt.DisplayRole, process[2])
            self.setItem(row, 2, item_cpu)

            # Multiply by 100 and add a percentage symbol
            item_cpu_percentage = QTableWidgetItem(f"{process[3]:.2f}%")
            self.setItem(row, 3, item_cpu_percentage)

            item_mem = QTableWidgetItem()
            item_mem.setData(Qt.DisplayRole, process[4])
            self.setItem(row, 4, item_mem)

            item_io = QTableWidgetItem()
            item_io.setData(Qt.DisplayRole, process[5])
            self.setItem(row, 5, item_io)

            self.setItem(row, 6, QTableWidgetItem(process[6]))
        self.setSortingEnabled(True)  # Enable sorting after update


if __name__ == '__main__':
    app = QApplication(sys.argv)
    table = ProcessTable(0, 5)
    table.show()
    sys.exit(app.exec_())
