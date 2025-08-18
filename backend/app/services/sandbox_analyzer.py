"""
Lightweight sandbox analysis service for FinGood platform.
Provides safe analysis of potentially dangerous file content without execution.
"""

import tempfile
import subprocess
import os
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import docker
import zipfile
import tarfile
import math
import mimetypes
import io
import pandas as pd

from app.core.config import settings
from app.core.audit_logger import security_audit_logger

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of sandbox analysis"""
    STATIC = "static"
    BEHAVIORAL = "behavioral"
    CONTAINER = "container"
    EMULATION = "emulation"


class RiskLevel(Enum):
    """Risk levels from sandbox analysis"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SandboxResult:
    """Result of sandbox analysis"""
    is_safe: bool
    risk_level: RiskLevel
    analysis_type: AnalysisType
    threats_detected: List[str]
    behavioral_indicators: List[str]
    static_analysis: Dict[str, Any]
    execution_trace: List[str]
    network_activity: List[str]
    file_system_changes: List[str]
    analysis_duration: float
    metadata: Dict[str, Any]
    errors: List[str]


class LightweightSandbox:
    """
    Lightweight sandbox analyzer for financial file uploads.
    Provides static analysis and safe emulation without full execution.
    """
    
    # Known safe file operations
    SAFE_OPERATIONS = {
        'read_file', 'parse_csv', 'validate_data', 'convert_encoding',
        'calculate_sum', 'format_date', 'trim_whitespace'
    }
    
    # Dangerous operations that trigger alerts
    DANGEROUS_OPERATIONS = {
        'execute_command', 'create_process', 'network_request', 'file_write',
        'registry_access', 'dll_load', 'memory_allocation', 'thread_creation',
        'socket_creation', 'pipe_creation', 'service_creation'
    }
    
    # File system paths that are dangerous to access
    DANGEROUS_PATHS = {
        '/etc/passwd', '/etc/shadow', '/root/', '/home/', '/var/',
        'C:\\Windows\\System32', 'C:\\Users\\', 'C:\\Program Files',
        '/Applications/', '/System/', '/Library/'
    }
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "fingood_sandbox"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        
        # Check if Docker is available for container analysis
        self.docker_available = self._check_docker_availability()
        
        # Initialize analysis tools
        self.static_analyzers = self._initialize_static_analyzers()
        
        logger.info(f"Sandbox initialized - Docker: {self.docker_available}, Static analyzers: {len(self.static_analyzers)}")
    
    async def analyze_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: Optional[str] = None,
        analysis_type: AnalysisType = AnalysisType.STATIC
    ) -> SandboxResult:
        """
        Perform sandbox analysis on file content.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            user_id: User ID for audit logging
            analysis_type: Type of analysis to perform
            
        Returns:
            SandboxResult with analysis findings
        """
        start_time = time.time()
        
        try:
            # Log analysis start
            security_audit_logger.log_sandbox_analysis_start(
                user_id=user_id,
                filename=filename,
                file_size=len(file_content),
                analysis_type=analysis_type.value
            )
            
            # Initialize result
            result = SandboxResult(
                is_safe=True,
                risk_level=RiskLevel.SAFE,
                analysis_type=analysis_type,
                threats_detected=[],
                behavioral_indicators=[],
                static_analysis={},
                execution_trace=[],
                network_activity=[],
                file_system_changes=[],
                analysis_duration=0.0,
                metadata={
                    'filename': filename,
                    'file_size': len(file_content),
                    'file_hash': hashlib.sha256(file_content).hexdigest()
                },
                errors=[]
            )
            
            # Perform analysis based on type
            if analysis_type == AnalysisType.STATIC:
                await self._static_analysis(file_content, filename, result)
            elif analysis_type == AnalysisType.BEHAVIORAL:
                await self._behavioral_analysis(file_content, filename, result)
            elif analysis_type == AnalysisType.CONTAINER and self.docker_available:
                await self._container_analysis(file_content, filename, result)
            elif analysis_type == AnalysisType.EMULATION:
                await self._emulation_analysis(file_content, filename, result)
            else:
                # Fallback to static analysis
                await self._static_analysis(file_content, filename, result)
            
            # Calculate final risk level
            self._calculate_risk_level(result)
            
            result.analysis_duration = time.time() - start_time
            
            # Log analysis completion
            security_audit_logger.log_sandbox_analysis_complete(
                user_id=user_id,
                filename=filename,
                risk_level=result.risk_level.value,
                threats_count=len(result.threats_detected),
                analysis_duration=result.analysis_duration,
                is_safe=result.is_safe
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Sandbox analysis failed for {filename}: {e}")
            
            error_result = SandboxResult(
                is_safe=False,
                risk_level=RiskLevel.CRITICAL,
                analysis_type=analysis_type,
                threats_detected=[],
                behavioral_indicators=[],
                static_analysis={},
                execution_trace=[],
                network_activity=[],
                file_system_changes=[],
                analysis_duration=time.time() - start_time,
                metadata={'filename': filename, 'file_size': len(file_content)},
                errors=[f"Analysis error: {str(e)}"]
            )
            
            security_audit_logger.log_sandbox_analysis_error(
                user_id=user_id,
                filename=filename,
                error=str(e)
            )
            
            return error_result
    
    async def _static_analysis(
        self,
        file_content: bytes,
        filename: str,
        result: SandboxResult
    ) -> None:
        """Perform static analysis without execution"""
        
        file_ext = Path(filename).suffix.lower()
        
        # Analyze file structure
        result.static_analysis['file_type'] = file_ext
        result.static_analysis['entropy'] = self._calculate_entropy(file_content)
        result.static_analysis['suspicious_strings'] = self._find_suspicious_strings(file_content)
        
        # Check for embedded content
        embedded_files = self._detect_embedded_files(file_content)
        if embedded_files:
            result.static_analysis['embedded_files'] = embedded_files
            result.behavioral_indicators.append(f"Contains {len(embedded_files)} embedded files")
        
        # Analyze archive contents if applicable
        if file_ext in ['.zip', '.tar', '.gz', '.bz2']:
            archive_analysis = await self._analyze_archive(file_content, filename)
            result.static_analysis['archive_contents'] = archive_analysis
            
            # Check for dangerous files in archive
            dangerous_files = [f for f in archive_analysis.get('files', []) 
                             if any(ext in f['name'].lower() for ext in ['.exe', '.dll', '.bat', '.sh', '.scr'])]
            
            if dangerous_files:
                result.threats_detected.append(f"Archive contains {len(dangerous_files)} potentially dangerous files")
        
        # Check for Office document macros
        if file_ext in ['.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt']:
            macro_analysis = self._analyze_office_macros(file_content)
            if macro_analysis['has_macros']:
                result.threats_detected.append("Office document contains macros")
                result.static_analysis['macro_analysis'] = macro_analysis
        
        # Financial file specific checks
        if file_ext == '.csv':
            csv_analysis = self._analyze_csv_content(file_content)
            result.static_analysis['csv_analysis'] = csv_analysis
            
            # Check for formula injection
            if csv_analysis.get('potential_formula_injection', False):
                result.threats_detected.append("Potential CSV formula injection detected")
    
    async def _behavioral_analysis(
        self,
        file_content: bytes,
        filename: str,
        result: SandboxResult
    ) -> None:
        """Analyze potential behavior without execution"""
        
        # First run static analysis
        await self._static_analysis(file_content, filename, result)
        
        # Analyze strings for behavioral indicators
        content_str = file_content.decode('utf-8', errors='ignore').lower()
        
        # Check for network-related strings
        network_indicators = [
            'http://', 'https://', 'ftp://', 'tcp://', 'udp://',
            'connect', 'socket', 'download', 'upload', 'curl', 'wget'
        ]
        
        found_network = [indicator for indicator in network_indicators if indicator in content_str]
        if found_network:
            result.behavioral_indicators.extend([f"Network indicator: {ind}" for ind in found_network])
        
        # Check for file system operations
        fs_indicators = [
            'delete', 'remove', 'mkdir', 'rmdir', 'copy', 'move',
            'create', 'write', 'append', 'truncate'
        ]
        
        found_fs = [indicator for indicator in fs_indicators if indicator in content_str]
        if found_fs:
            result.behavioral_indicators.extend([f"File system indicator: {ind}" for ind in found_fs])
        
        # Check for system commands
        system_commands = [
            'cmd.exe', 'powershell', 'bash', 'sh', 'system(',
            'exec(', 'eval(', 'spawn', 'fork'
        ]
        
        found_commands = [cmd for cmd in system_commands if cmd in content_str]
        if found_commands:
            result.threats_detected.extend([f"System command: {cmd}" for cmd in found_commands])
        
        # Check for credential harvesting patterns
        credential_patterns = [
            'password', 'passwd', 'credentials', 'login', 'auth',
            'token', 'key', 'secret', 'private'
        ]
        
        credential_count = sum(1 for pattern in credential_patterns if pattern in content_str)
        if credential_count > 3:
            result.behavioral_indicators.append(f"High credential-related content: {credential_count} patterns")
    
    async def _container_analysis(
        self,
        file_content: bytes,
        filename: str,
        result: SandboxResult
    ) -> None:
        """Analyze file in isolated Docker container"""
        
        if not self.docker_available:
            result.errors.append("Docker not available for container analysis")
            await self._static_analysis(file_content, filename, result)
            return
        
        try:
            client = docker.from_env()
            
            # Create temporary file
            temp_file = self.temp_dir / f"sandbox_{int(time.time())}_{filename}"
            with open(temp_file, 'wb') as f:
                f.write(file_content)
            
            # Run analysis in container
            container = client.containers.run(
                'alpine:latest',
                command=f'file /tmp/{filename}',
                volumes={str(temp_file): {'bind': f'/tmp/{filename}', 'mode': 'ro'}},
                detach=True,
                remove=True,
                network_mode='none',  # No network access
                mem_limit='128m',     # Memory limit
                cpu_period=100000,    # CPU limit
                cpu_quota=50000
            )
            
            # Wait for completion with timeout
            try:
                container.wait(timeout=30)
                logs = container.logs().decode('utf-8')
                result.execution_trace.append(f"Container analysis: {logs}")
            except Exception as e:
                result.errors.append(f"Container analysis timeout: {str(e)}")
            
        except Exception as e:
            result.errors.append(f"Container analysis failed: {str(e)}")
            logger.error(f"Container analysis failed: {e}")
        
        finally:
            # Clean up
            try:
                temp_file.unlink()
            except:
                pass
        
        # Fallback to static analysis
        await self._static_analysis(file_content, filename, result)
    
    async def _emulation_analysis(
        self,
        file_content: bytes,
        filename: str,
        result: SandboxResult
    ) -> None:
        """Emulate file processing to detect dangerous operations"""
        
        # Start with behavioral analysis
        await self._behavioral_analysis(file_content, filename, result)
        
        file_ext = Path(filename).suffix.lower()
        
        # Emulate CSV processing
        if file_ext == '.csv':
            try:
                emulation_result = self._emulate_csv_processing(file_content)
                result.execution_trace.extend(emulation_result['operations'])
                
                if emulation_result['dangerous_operations']:
                    result.threats_detected.extend(emulation_result['dangerous_operations'])
                
            except Exception as e:
                result.errors.append(f"CSV emulation failed: {str(e)}")
        
        # Emulate archive extraction
        elif file_ext in ['.zip', '.tar', '.gz']:
            try:
                emulation_result = self._emulate_archive_extraction(file_content)
                result.file_system_changes.extend(emulation_result['would_create'])
                
                if emulation_result['dangerous_paths']:
                    result.threats_detected.extend([f"Would access dangerous path: {path}" 
                                                  for path in emulation_result['dangerous_paths']])
                
            except Exception as e:
                result.errors.append(f"Archive emulation failed: {str(e)}")
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0
        
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        entropy = 0
        data_len = len(data)
        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _find_suspicious_strings(self, file_content: bytes) -> List[str]:
        """Find suspicious strings in file content"""
        
        content_str = file_content.decode('utf-8', errors='ignore').lower()
        suspicious = []
        
        # Malware family names
        malware_families = [
            'zeus', 'carbanak', 'dridex', 'emotet', 'trickbot',
            'bankbot', 'shylock', 'dyre', 'neverquest'
        ]
        
        for family in malware_families:
            if family in content_str:
                suspicious.append(f"Malware family reference: {family}")
        
        # Dangerous APIs
        dangerous_apis = [
            'createprocess', 'shellexecute', 'winexec', 'virtualalloc',
            'writeprocessmemory', 'createthread', 'loadlibrary'
        ]
        
        for api in dangerous_apis:
            if api in content_str:
                suspicious.append(f"Dangerous API: {api}")
        
        return suspicious
    
    def _detect_embedded_files(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Detect embedded files within the content"""
        
        embedded = []
        
        # Common file signatures
        signatures = [
            (b'MZ', 'PE Executable'),
            (b'\x7fELF', 'ELF Executable'),
            (b'%PDF', 'PDF Document'),
            (b'PK\x03\x04', 'ZIP Archive'),
            (b'\xff\xd8\xff', 'JPEG Image'),
            (b'\x89PNG', 'PNG Image'),
        ]
        
        for sig, file_type in signatures:
            positions = []
            start = 0
            while True:
                pos = file_content.find(sig, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
            
            if len(positions) > 1:  # Multiple instances suggest embedded files
                embedded.append({
                    'type': file_type,
                    'signature': sig.hex(),
                    'positions': positions[:5],  # Limit to first 5
                    'count': len(positions)
                })
        
        return embedded
    
    async def _analyze_archive(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Analyze archive contents safely"""
        
        analysis = {
            'files': [],
            'total_size': 0,
            'compressed_ratio': 0,
            'suspicious_files': []
        }
        
        try:
            # Create temporary file
            temp_file = self.temp_dir / f"archive_{int(time.time())}.tmp"
            with open(temp_file, 'wb') as f:
                f.write(file_content)
            
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.zip':
                with zipfile.ZipFile(temp_file, 'r') as zf:
                    for info in zf.infolist():
                        file_info = {
                            'name': info.filename,
                            'size': info.file_size,
                            'compressed_size': info.compress_size,
                            'is_dir': info.is_dir()
                        }
                        analysis['files'].append(file_info)
                        analysis['total_size'] += info.file_size
                        
                        # Check for suspicious files
                        if any(ext in info.filename.lower() 
                              for ext in ['.exe', '.dll', '.bat', '.scr', '.vbs']):
                            analysis['suspicious_files'].append(info.filename)
            
            elif file_ext in ['.tar', '.gz', '.bz2']:
                with tarfile.open(temp_file, 'r:*') as tf:
                    for member in tf.getmembers():
                        file_info = {
                            'name': member.name,
                            'size': member.size,
                            'is_dir': member.isdir()
                        }
                        analysis['files'].append(file_info)
                        analysis['total_size'] += member.size
                        
                        if any(ext in member.name.lower() 
                              for ext in ['.exe', '.dll', '.bat', '.scr', '.vbs']):
                            analysis['suspicious_files'].append(member.name)
            
            # Calculate compression ratio
            if len(file_content) > 0:
                analysis['compressed_ratio'] = analysis['total_size'] / len(file_content)
            
        except Exception as e:
            analysis['error'] = str(e)
        
        finally:
            try:
                temp_file.unlink()
            except:
                pass
        
        return analysis
    
    def _analyze_office_macros(self, file_content: bytes) -> Dict[str, Any]:
        """Analyze Office documents for macros"""
        
        analysis = {
            'has_macros': False,
            'macro_count': 0,
            'suspicious_macros': []
        }
        
        # Look for VBA project signatures
        if b'vbaProject' in file_content or b'macros/' in file_content:
            analysis['has_macros'] = True
            
            # Count potential macro modules
            macro_indicators = [b'Sub ', b'Function ', b'Private Sub', b'Public Sub']
            for indicator in macro_indicators:
                analysis['macro_count'] += file_content.count(indicator)
            
            # Check for suspicious macro content
            suspicious_patterns = [
                b'Shell', b'CreateObject', b'WScript', b'cmd.exe',
                b'powershell', b'DownloadFile', b'UrlDownloadToFile'
            ]
            
            for pattern in suspicious_patterns:
                if pattern in file_content:
                    analysis['suspicious_macros'].append(pattern.decode('utf-8', errors='ignore'))
        
        return analysis
    
    def _analyze_csv_content(self, file_content: bytes) -> Dict[str, Any]:
        """Analyze CSV content for security issues"""
        
        analysis = {
            'potential_formula_injection': False,
            'suspicious_formulas': [],
            'large_cells': [],
            'encoding_issues': False
        }
        
        try:
            content_str = file_content.decode('utf-8', errors='ignore')
            lines = content_str.split('\n')
            
            for line_num, line in enumerate(lines[:100]):  # Check first 100 lines
                cells = line.split(',')
                
                for cell_num, cell in enumerate(cells):
                    cell = cell.strip()
                    
                    # Check for formula injection
                    if cell.startswith(('=', '+', '-', '@')):
                        analysis['potential_formula_injection'] = True
                        analysis['suspicious_formulas'].append({
                            'line': line_num + 1,
                            'cell': cell_num + 1,
                            'content': cell[:50]  # Truncate for safety
                        })
                    
                    # Check for unusually large cells
                    if len(cell) > 1000:
                        analysis['large_cells'].append({
                            'line': line_num + 1,
                            'cell': cell_num + 1,
                            'size': len(cell)
                        })
            
        except UnicodeDecodeError:
            analysis['encoding_issues'] = True
        
        return analysis
    
    def _emulate_csv_processing(self, file_content: bytes) -> Dict[str, Any]:
        """Emulate CSV processing to detect dangerous operations"""
        
        result = {
            'operations': [],
            'dangerous_operations': []
        }
        
        try:
            content_str = file_content.decode('utf-8', errors='ignore')
            lines = content_str.split('\n')
            
            result['operations'].append(f"Would process {len(lines)} lines")
            
            # Check each line for potential dangers
            for line_num, line in enumerate(lines[:50]):  # Limit analysis
                cells = line.split(',')
                
                for cell in cells:
                    cell = cell.strip()
                    
                    # Check for formula that would execute
                    if cell.startswith('=') and any(func in cell.upper() 
                                                   for func in ['HYPERLINK', 'WEBSERVICE', 'IMPORTDATA']):
                        result['dangerous_operations'].append(
                            f"Line {line_num + 1}: Dangerous formula {cell[:30]}..."
                        )
                    
                    # Check for system commands
                    if any(cmd in cell.lower() for cmd in ['cmd.exe', 'powershell', 'bash']):
                        result['dangerous_operations'].append(
                            f"Line {line_num + 1}: System command reference"
                        )
            
        except Exception as e:
            result['operations'].append(f"Emulation error: {str(e)}")
        
        return result
    
    def _emulate_archive_extraction(self, file_content: bytes) -> Dict[str, Any]:
        """Emulate archive extraction to detect dangerous paths"""
        
        result = {
            'would_create': [],
            'dangerous_paths': []
        }
        
        try:
            # Try to analyze as ZIP
            temp_file = self.temp_dir / f"emulate_{int(time.time())}.zip"
            with open(temp_file, 'wb') as f:
                f.write(file_content)
            
            with zipfile.ZipFile(temp_file, 'r') as zf:
                for info in zf.infolist():
                    path = info.filename
                    result['would_create'].append(path)
                    
                    # Check for path traversal
                    if '..' in path or path.startswith('/') or '\\' in path:
                        result['dangerous_paths'].append(path)
                    
                    # Check for system paths
                    if any(dangerous in path.lower() for dangerous in self.DANGEROUS_PATHS):
                        result['dangerous_paths'].append(path)
            
        except Exception:
            # Try as TAR
            try:
                with tarfile.open(fileobj=io.BytesIO(file_content), mode='r:*') as tf:
                    for member in tf.getmembers():
                        path = member.name
                        result['would_create'].append(path)
                        
                        if '..' in path or path.startswith('/'):
                            result['dangerous_paths'].append(path)
            except Exception:
                pass
        
        finally:
            try:
                temp_file.unlink()
            except:
                pass
        
        return result
    
    def _calculate_risk_level(self, result: SandboxResult) -> None:
        """Calculate overall risk level based on findings"""
        
        threat_count = len(result.threats_detected)
        behavioral_count = len(result.behavioral_indicators)
        
        # Start with safe
        risk_score = 0
        
        # Add points for threats
        risk_score += threat_count * 10
        risk_score += behavioral_count * 3
        
        # Add points for high entropy (potential encryption)
        entropy = result.static_analysis.get('entropy', 0)
        if entropy > 7.5:
            risk_score += 5
        
        # Add points for embedded files
        embedded_files = result.static_analysis.get('embedded_files', [])
        risk_score += len(embedded_files) * 8
        
        # Add points for suspicious strings
        suspicious_strings = result.static_analysis.get('suspicious_strings', [])
        risk_score += len(suspicious_strings) * 5
        
        # Determine risk level
        if risk_score == 0:
            result.risk_level = RiskLevel.SAFE
            result.is_safe = True
        elif risk_score <= 10:
            result.risk_level = RiskLevel.LOW
            result.is_safe = True
        elif risk_score <= 25:
            result.risk_level = RiskLevel.MEDIUM
            result.is_safe = False
        elif risk_score <= 50:
            result.risk_level = RiskLevel.HIGH
            result.is_safe = False
        else:
            result.risk_level = RiskLevel.CRITICAL
            result.is_safe = False
    
    def _check_docker_availability(self) -> bool:
        """Check if Docker is available"""
        try:
            import docker
            client = docker.from_env()
            client.ping()
            return True
        except:
            return False
    
    def _initialize_static_analyzers(self) -> List[str]:
        """Initialize available static analysis tools"""
        analyzers = []
        
        # Check for system tools
        tools = ['file', 'strings', 'hexdump', 'objdump']
        for tool in tools:
            try:
                subprocess.run([tool, '--help'], capture_output=True, timeout=5)
                analyzers.append(tool)
            except:
                pass
        
        return analyzers


# Convenience function
async def analyze_file_in_sandbox(
    file_content: bytes,
    filename: str,
    user_id: Optional[str] = None,
    analysis_type: AnalysisType = AnalysisType.STATIC
) -> SandboxResult:
    """Convenience function to analyze file in sandbox"""
    sandbox = LightweightSandbox()
    return await sandbox.analyze_file(file_content, filename, user_id, analysis_type)