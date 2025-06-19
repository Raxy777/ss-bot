# supabase_client.py - Supabase client setup
import os
from supabase import create_client, Client
from datetime import datetime
import uuid
import json

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class DisasterReportService:
    def __init__(self):
        self.supabase = supabase
    
    def create_report(self, report_data):
        """Create a new disaster report in Supabase"""
        try:
            # Generate unique report ID
            report_id = str(uuid.uuid4())[:8].upper()
            
            # Prepare data for insertion
            db_data = {
                'id': report_id,
                'user_id': str(report_data['user_id']),
                'username': report_data.get('username', 'Anonymous'),
                'disaster_type': report_data['disaster_type'],
                'severity': report_data['severity'],
                'latitude': float(report_data['latitude']),
                'longitude': float(report_data['longitude']),
                'description': report_data.get('description', ''),
                'photos': json.dumps(report_data.get('photos', [])),
                'status': 'Pending',
                'source': 'Telegram Bot',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert into Supabase
            result = self.supabase.table('disaster_reports').insert(db_data).execute()
            
            if result.data:
                return {
                    'success': True,
                    'id': report_id,
                    'data': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create report'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_reports(self, user_id, limit=10):
        """Get reports for a specific user"""
        try:
            result = self.supabase.table('disaster_reports')\
                .select('*')\
                .eq('user_id', str(user_id))\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return {
                'success': True,
                'data': result.data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_report_by_id(self, report_id):
        """Get a specific report by ID"""
        try:
            result = self.supabase.table('disaster_reports')\
                .select('*')\
                .eq('id', report_id)\
                .execute()
            
            if result.data:
                return {
                    'success': True,
                    'data': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Report not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_report_status(self, report_id, status):
        """Update report status"""
        try:
            result = self.supabase.table('disaster_reports')\
                .update({
                    'status': status,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', report_id)\
                .execute()
            
            if result.data:
                return {
                    'success': True,
                    'data': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Report not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_all_reports(self, filters=None, limit=50):
        """Get all reports with optional filters"""
        try:
            query = self.supabase.table('disaster_reports').select('*')
            
            if filters:
                if 'severity' in filters:
                    query = query.eq('severity', filters['severity'])
                if 'disaster_type' in filters:
                    query = query.eq('disaster_type', filters['disaster_type'])
                if 'status' in filters:
                    query = query.eq('status', filters['status'])
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            return {
                'success': True,
                'data': result.data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_reports_by_location(self, lat, lng, radius_km=10):
        """Get reports within a certain radius (simplified version)"""
        try:
            # Note: For more accurate geo-queries, you might want to use PostGIS functions
            # This is a simplified version
            result = self.supabase.table('disaster_reports')\
                .select('*')\
                .execute()
            
            # Filter by distance (basic implementation)
            filtered_reports = []
            for report in result.data:
                if self._calculate_distance(lat, lng, report['latitude'], report['longitude']) <= radius_km:
                    filtered_reports.append(report)
            
            return {
                'success': True,
                'data': filtered_reports
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in kilometers"""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

# Emergency notification service
class EmergencyNotificationService:
    def __init__(self):
        self.supabase = supabase
    
    def trigger_emergency_alert(self, report_data):
        """Trigger emergency notifications for critical reports"""
        try:
            # Log emergency alert
            alert_data = {
                'report_id': report_data['id'],
                'alert_type': 'Critical Disaster Report',
                'severity': report_data['severity'],
                'location': f"{report_data['latitude']}, {report_data['longitude']}",
                'disaster_type': report_data['disaster_type'],
                'description': report_data.get('description', ''),
                'status': 'Active',
                'created_at': datetime.now().isoformat()
            }
            
            # Store alert in emergency_alerts table
            result = self.supabase.table('emergency_alerts').insert(alert_data).execute()
            
            # Here you can add integrations with:
            # - SMS services (Twilio)
            # - Email notifications
            # - Push notifications
            # - Emergency services API
            # - Discord/Slack webhooks
            
            print(f"🚨 EMERGENCY ALERT TRIGGERED 🚨")
            print(f"Report ID: {report_data['id']}")
            print(f"Type: {report_data['disaster_type']}")
            print(f"Severity: {report_data['severity']}")
            print(f"Location: {report_data['latitude']}, {report_data['longitude']}")
            
            return {
                'success': True,
                'alert_id': result.data[0]['id'] if result.data else None
            }
            
        except Exception as e:
            print(f"Error triggering emergency alert: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Initialize services
disaster_service = DisasterReportService()
emergency_service = EmergencyNotificationService()