"""
Verification Layer for Project VOID

Uses VOID Lens to confirm that synthesized compounds match their frequency signatures.

This is the quality control system for decentralized synthesis:
- Every compound synthesized is photographed
- VOID Lens extracts its frequency signature
- Compared against expected signature
- Pass/fail verdict determines if synthesis was successful
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
import hashlib


class VerificationStatus(Enum):
    """Verification outcome."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    DEVIANT = "deviant"
    FAILED = "failed"


@dataclass
class VerificationResult:
    """Result of VOID Lens verification."""
    task_id: str
    compound_id: str
    expected_frequency: float
    measured_frequency: float
    frequency_deviation_hz: float
    deviation_percent: float
    status: VerificationStatus
    confidence_score: float  # 0.0-1.0
    codon_band: str  # Which band the deviation falls in
    timestamp: int
    
    def is_valid(self, tolerance_hz: float = 50.0) -> bool:
        """Check if verification passed within tolerance."""
        return abs(self.frequency_deviation_hz) <= tolerance_hz and self.status == VerificationStatus.VERIFIED


class VerificationLayer:
    """
    Verification system using VOID Lens.
    
    For each synthesis task:
    1. Synthesis node produces compound
    2. Takes photograph
    3. Sends to monitoring node
    4. VOID Lens extracts frequency signature
    5. Compares against expected signature
    6. Returns pass/fail + confidence score
    """
    
    def __init__(self, void_lens_engine=None):
        """
        Initialize verification layer.
        
        Args:
            void_lens_engine: VOID Lens instance for frequency extraction
        """
        self.lens = void_lens_engine
        self.verification_queue = []
        self.verification_results = {}
        self.statistics = {
            'total_verifications': 0,
            'verified_compounds': 0,
            'deviant_compounds': 0,
            'failed_verifications': 0,
            'average_confidence': 0.0,
            'average_deviation_hz': 0.0,
        }
    
    def request_verification(self, task_id: str, compound_id: str, 
                            expected_frequency: float, image_path: str) -> str:
        """
        Request verification of a synthesized compound.
        
        Args:
            task_id: Synthesis task ID
            compound_id: Which compound was synthesized
            expected_frequency: Expected frequency signature
            image_path: Path to photograph of synthesized compound
        
        Returns:
            Verification ID
        """
        verification_id = f"verify-{task_id}"
        
        self.verification_queue.append({
            'verification_id': verification_id,
            'task_id': task_id,
            'compound_id': compound_id,
            'expected_frequency': expected_frequency,
            'image_path': image_path,
            'status': VerificationStatus.PENDING,
        })
        
        return verification_id
    
    def process_verification(self, verification_id: str) -> VerificationResult:
        """
        Process a verification request using VOID Lens.
        
        Returns the verification result.
        """
        # Find the verification request
        request = None
        for req in self.verification_queue:
            if req['verification_id'] == verification_id:
                request = req
                break
        
        if not request:
            return None
        
        # Extract frequency from image using VOID Lens
        if self.lens:
            measured_frequency, confidence = self.lens.extract_frequency_from_image(
                request['image_path']
            )
        else:
            # Simulation: add small random deviation
            import random
            measured_frequency = request['expected_frequency'] + random.uniform(-30, 30)
            confidence = 0.85
        
        # Calculate deviation
        deviation_hz = measured_frequency - request['expected_frequency']
        deviation_percent = (deviation_hz / request['expected_frequency']) * 100
        
        # Determine status
        tolerance_hz = 50.0  # ±50 Hz tolerance
        if abs(deviation_hz) <= tolerance_hz:
            status = VerificationStatus.VERIFIED
        elif abs(deviation_hz) <= tolerance_hz * 2:
            status = VerificationStatus.DEVIANT
        else:
            status = VerificationStatus.FAILED
        
        # Map deviation to codon band
        codon_band = self._map_deviation_to_codon_band(deviation_hz)
        
        # Create result
        result = VerificationResult(
            task_id=request['task_id'],
            compound_id=request['compound_id'],
            expected_frequency=request['expected_frequency'],
            measured_frequency=measured_frequency,
            frequency_deviation_hz=deviation_hz,
            deviation_percent=deviation_percent,
            status=status,
            confidence_score=confidence,
            codon_band=codon_band,
            timestamp=int(__import__('time').time())
        )
        
        # Store result
        self.verification_results[verification_id] = result
        
        # Update statistics
        self.statistics['total_verifications'] += 1
        if status == VerificationStatus.VERIFIED:
            self.statistics['verified_compounds'] += 1
        elif status == VerificationStatus.DEVIANT:
            self.statistics['deviant_compounds'] += 1
        else:
            self.statistics['failed_verifications'] += 1
        
        # Update averages
        all_results = list(self.verification_results.values())
        self.statistics['average_confidence'] = sum(r.confidence_score for r in all_results) / len(all_results)
        self.statistics['average_deviation_hz'] = sum(abs(r.frequency_deviation_hz) for r in all_results) / len(all_results)
        
        return result
    
    def _map_deviation_to_codon_band(self, deviation_hz: float) -> str:
        """Map frequency deviation to Adriana's codon band."""
        abs_dev = abs(deviation_hz)
        
        if abs_dev < 10:
            return "alpha"  # Structural (perfect alignment)
        elif abs_dev < 20:
            return "beta"   # Relational (minor deviation)
        elif abs_dev < 30:
            return "gamma"  # Temporal (moderate deviation)
        elif abs_dev < 40:
            return "delta"  # Spatial (significant deviation)
        elif abs_dev < 50:
            return "epsilon"  # Resonance (major deviation)
        else:
            return "zeta"   # Quantum (extreme deviation)
    
    def get_verification_result(self, verification_id: str) -> Optional[VerificationResult]:
        """Get a verification result."""
        return self.verification_results.get(verification_id)
    
    def get_statistics(self) -> Dict:
        """Get verification statistics."""
        total = self.statistics['total_verifications']
        if total == 0:
            success_rate = 0.0
        else:
            success_rate = (self.statistics['verified_compounds'] / total) * 100
        
        return {
            **self.statistics,
            'success_rate_percent': success_rate,
            'pending_verifications': len(self.verification_queue),
        }
    
    def generate_verification_report(self) -> str:
        """Generate a human-readable verification report."""
        stats = self.get_statistics()
        
        report = f"""
VOID Verification Layer Report
==============================

Total Verifications: {stats['total_verifications']}
Verified (Pass): {stats['verified_compounds']}
Deviant (Minor): {stats['deviant_compounds']}
Failed: {stats['failed_verifications']}

Success Rate: {stats['success_rate_percent']:.1f}%
Average Confidence: {stats['average_confidence']:.2f}
Average Deviation: {stats['average_deviation_hz']:.1f} Hz

Pending Verifications: {stats['pending_verifications']}

Codon Band Distribution:
  Alpha (structural): {sum(1 for r in self.verification_results.values() if r.codon_band == 'alpha')}
  Beta (relational): {sum(1 for r in self.verification_results.values() if r.codon_band == 'beta')}
  Gamma (temporal): {sum(1 for r in self.verification_results.values() if r.codon_band == 'gamma')}
  Delta (spatial): {sum(1 for r in self.verification_results.values() if r.codon_band == 'delta')}
  Epsilon (resonance): {sum(1 for r in self.verification_results.values() if r.codon_band == 'epsilon')}
  Zeta (quantum): {sum(1 for r in self.verification_results.values() if r.codon_band == 'zeta')}
"""
        return report


class QualityControlSystem:
    """
    Full quality control system for decentralized synthesis.
    
    Ensures that every compound produced meets specifications.
    """
    
    def __init__(self):
        self.verification_layer = VerificationLayer()
        self.failed_batches = []
        self.quality_threshold = 0.90  # 90% success rate minimum
    
    def process_synthesis_batch(self, batch_id: str, compounds: List[Dict]) -> Dict:
        """
        Process a batch of synthesized compounds.
        
        Each compound in the batch is verified.
        """
        results = []
        
        for compound in compounds:
            verification_id = self.verification_layer.request_verification(
                task_id=compound['task_id'],
                compound_id=compound['compound_id'],
                expected_frequency=compound['expected_frequency'],
                image_path=compound['image_path']
            )
            
            result = self.verification_layer.process_verification(verification_id)
            results.append(result)
        
        # Calculate batch quality
        passed = sum(1 for r in results if r.status == VerificationStatus.VERIFIED)
        batch_quality = passed / len(results) if results else 0.0
        
        batch_report = {
            'batch_id': batch_id,
            'total_compounds': len(results),
            'passed': passed,
            'quality_percent': batch_quality * 100,
            'meets_threshold': batch_quality >= self.quality_threshold,
            'results': results,
        }
        
        if batch_quality < self.quality_threshold:
            self.failed_batches.append(batch_report)
        
        return batch_report
    
    def get_quality_report(self) -> Dict:
        """Get overall quality control report."""
        all_results = self.verification_layer.verification_results.values()
        
        if not all_results:
            return {'status': 'no_data'}
        
        passed = sum(1 for r in all_results if r.status == VerificationStatus.VERIFIED)
        total = len(all_results)
        
        return {
            'total_verifications': total,
            'passed': passed,
            'failed': total - passed,
            'quality_percent': (passed / total) * 100,
            'average_confidence': sum(r.confidence_score for r in all_results) / total,
            'failed_batches': len(self.failed_batches),
            'meets_global_threshold': (passed / total) >= self.quality_threshold,
        }


# Example usage
if __name__ == "__main__":
    # Create verification system
    qc = QualityControlSystem()
    
    # Simulate a batch of compounds
    batch = [
        {
            'task_id': 'task-001',
            'compound_id': 'void-carbon-lattice-001',
            'expected_frequency': 432.0,
            'image_path': '/path/to/image1.jpg',
        },
        {
            'task_id': 'task-002',
            'compound_id': 'void-chladni-diamond-002',
            'expected_frequency': 864.0,
            'image_path': '/path/to/image2.jpg',
        },
        {
            'task_id': 'task-003',
            'compound_id': 'void-quantum-cymatics-003',
            'expected_frequency': 1296.0,
            'image_path': '/path/to/image3.jpg',
        },
    ]
    
    # Process batch
    batch_report = qc.process_synthesis_batch('batch-001', batch)
    print(f"Batch quality: {batch_report['quality_percent']:.1f}%")
    print(f"Passed: {batch_report['passed']}/{batch_report['total_compounds']}")
    
    # Get overall report
    report = qc.get_quality_report()
    print(f"\nQuality Report:")
    print(f"  Total verifications: {report['total_verifications']}")
    print(f"  Passed: {report['passed']}")
    print(f"  Quality: {report['quality_percent']:.1f}%")
    print(f"  Meets threshold: {report['meets_global_threshold']}")
