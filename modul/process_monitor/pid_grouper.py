"""
PID Grouper Module
PID'e göre süreçleri gruplandırma ve analiz işlemleri
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PIDGrouper:
    """PID'e göre süreçleri gruplandırma sınıfı"""
    
    def __init__(self):
        """PIDGrouper sınıfını başlat"""
        self.logger = logger
    
    def group_by_pid(self, connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bağlantıları PID'e göre grupla
        
        Args:
            connections: Bağlantı listesi
            
        Returns:
            PID'e göre gruplandırılmış süreç listesi
        """
        try:
            pid_groups = {}
            
            for conn in connections:
                pid = conn.get('pid', '-')
                
                # PID yoksa veya '-' ise atla
                if not pid or pid == '-':
                    continue
                
                # PID grubu yoksa oluştur
                if pid not in pid_groups:
                    pid_groups[pid] = self._create_pid_group(pid, conn)
                
                # Bağlantı bilgilerini ekle
                self._add_connection_to_group(pid_groups[pid], conn)
            
            # Liste olarak dönüştür ve bağlantı sayısına göre sırala
            result = sorted(pid_groups.values(), key=lambda x: x['total_connections'], reverse=True)
            
            self.logger.info(f"PID gruplandırma tamamlandı: {len(result)} farklı PID bulundu")
            
            return result
            
        except Exception as e:
            self.logger.error(f"PID gruplandırma hatası: {str(e)}")
            raise
    
    def _create_pid_group(self, pid: int, conn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yeni bir PID grubu oluştur
        
        Args:
            pid: Process ID
            conn: İlk bağlantı bilgisi
            
        Returns:
            PID grup dictionary'si
        """
        process_details = conn.get('process_details', {})
        
        return {
            'pid': pid,
            'process_name': conn.get('process_name', 'Unknown'),
            'connections': [],
            'total_connections': 0,
            'protocols': {},
            'statuses': {},
            'cpu_percent': process_details.get('cpu_percent', 0),
            'memory_percent': process_details.get('memory_percent', 0),
            'memory_mb': process_details.get('memory_mb', 0),
            'username': process_details.get('username', 'N/A'),
            'create_time': process_details.get('create_time', 'N/A'),
            'num_threads': process_details.get('num_threads', 0),
        }
    
    def _add_connection_to_group(self, group: Dict[str, Any], conn: Dict[str, Any]) -> None:
        """
        Bir bağlantıyı gruba ekle ve istatistikleri güncelle
        
        Args:
            group: PID grubu
            conn: Bağlantı bilgisi
        """
        # Bağlantı bilgilerini ekle
        group['connections'].append({
            'protocol': conn.get('protocol', 'UNKNOWN'),
            'local_address': conn.get('local_address', 'N/A'),
            'remote_address': conn.get('remote_address', 'N/A'),
            'status': conn.get('status', 'UNKNOWN'),
            'local_port': self._extract_port(conn.get('local_address', '')),
            'remote_port': self._extract_port(conn.get('remote_address', '')),
        })
        
        # Toplam bağlantı sayısını artır
        group['total_connections'] += 1
        
        # Protokol istatistiklerini güncelle
        protocol = conn.get('protocol', 'UNKNOWN')
        group['protocols'][protocol] = group['protocols'].get(protocol, 0) + 1
        
        # Durum istatistiklerini güncelle
        status = conn.get('status', 'UNKNOWN')
        group['statuses'][status] = group['statuses'].get(status, 0) + 1
    
    def _extract_port(self, address: str) -> str:
        """
        Adres string'inden port numarasını çıkar
        
        Args:
            address: Adres string'i (örn: "192.168.1.1:8080")
            
        Returns:
            Port numarası veya 'N/A'
        """
        try:
            if ':' in address:
                return address.split(':')[-1]
            return 'N/A'
        except:
            return 'N/A'
    
    def get_statistics(self, grouped_processes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gruplandırılmış süreçler için genel istatistikler oluştur
        
        Args:
            grouped_processes: Gruplandırılmış süreç listesi
            
        Returns:
            İstatistik dictionary'si
        """
        try:
            total_processes = len(grouped_processes)
            total_connections = sum(p['total_connections'] for p in grouped_processes)
            
            # En çok bağlantısı olan süreçler (top 5)
            top_processes = sorted(
                grouped_processes, 
                key=lambda x: x['total_connections'], 
                reverse=True
            )[:5]
            
            # Protokol dağılımı
            protocol_distribution = {}
            for process in grouped_processes:
                for protocol, count in process['protocols'].items():
                    protocol_distribution[protocol] = protocol_distribution.get(protocol, 0) + count
            
            # Durum dağılımı
            status_distribution = {}
            for process in grouped_processes:
                for status, count in process['statuses'].items():
                    status_distribution[status] = status_distribution.get(status, 0) + count
            
            # Toplam CPU ve Memory kullanımı
            total_cpu = sum(p['cpu_percent'] for p in grouped_processes)
            total_memory = sum(p['memory_mb'] for p in grouped_processes)
            
            return {
                'total_processes': total_processes,
                'total_connections': total_connections,
                'top_processes': [
                    {
                        'pid': p['pid'],
                        'name': p['process_name'],
                        'connections': p['total_connections']
                    } for p in top_processes
                ],
                'protocol_distribution': protocol_distribution,
                'status_distribution': status_distribution,
                'total_cpu_percent': round(total_cpu, 2),
                'total_memory_mb': round(total_memory, 2),
                'avg_connections_per_process': round(total_connections / total_processes, 2) if total_processes > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"İstatistik oluşturma hatası: {str(e)}")
            return {}
    
    def filter_by_criteria(
        self, 
        grouped_processes: List[Dict[str, Any]], 
        min_connections: int = None,
        protocol: str = None,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """
        Gruplandırılmış süreçleri kriterlere göre filtrele
        
        Args:
            grouped_processes: Gruplandırılmış süreç listesi
            min_connections: Minimum bağlantı sayısı
            protocol: Protokol filtresi (TCP, UDP, etc.)
            status: Durum filtresi (ESTABLISHED, LISTEN, etc.)
            
        Returns:
            Filtrelenmiş süreç listesi
        """
        try:
            result = grouped_processes
            
            # Minimum bağlantı sayısına göre filtrele
            if min_connections is not None:
                result = [p for p in result if p['total_connections'] >= min_connections]
            
            # Protokole göre filtrele
            if protocol:
                result = [p for p in result if protocol in p['protocols']]
            
            # Duruma göre filtrele
            if status:
                result = [p for p in result if status in p['statuses']]
            
            self.logger.info(f"Filtreleme tamamlandı: {len(result)} süreç kaldı")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Filtreleme hatası: {str(e)}")
            return grouped_processes


# Global PIDGrouper instance
pid_grouper = PIDGrouper()

