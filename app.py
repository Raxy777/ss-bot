# app.py - Updated Flask routes with Supabase integration
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase_client import disaster_service, emergency_service
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/api/reports', methods=['POST'])
def create_report():
    """Create a new disaster report from Telegram bot"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'disaster_type', 'severity', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create report using Supabase service
        result = disaster_service.create_report(data)
        
        if result['success']:
            report_data = result['data']
            
            # Trigger emergency alerts for critical reports
            if data['severity'] == 'Critical':
                emergency_service.trigger_emergency_alert(report_data)
            
            return jsonify({
                'id': result['id'],
                'status': 'success',
                'message': 'Report created successfully',
                'data': report_data
            }), 201
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/user/<user_id>', methods=['GET'])
def get_user_reports(user_id):
    """Get reports for a specific user"""
    try:
        limit = request.args.get('limit', 10, type=int)
        result = disaster_service.get_user_reports(user_id, limit)
        
        if result['success']:
            return jsonify(result['data']), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    """Get a specific report by ID"""
    try:
        result = disaster_service.get_report_by_id(report_id)
        
        if result['success']:
            return jsonify(result['data']), 200
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<report_id>/status', methods=['PUT'])
def update_report_status(report_id):
    """Update report status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        valid_statuses = ['Pending', 'In Progress', 'Resolved', 'Cancelled']
        if not new_status or new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        result = disaster_service.update_report_status(report_id, new_status)
        
        if result['success']:
            return jsonify({
                'message': 'Status updated successfully',
                'data': result['data']
            }), 200
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def get_all_reports():
    """Get all reports with optional filters"""
    try:
        # Get query parameters for filtering
        filters = {}
        if request.args.get('severity'):
            filters['severity'] = request.args.get('severity')
        if request.args.get('disaster_type'):
            filters['disaster_type'] = request.args.get('disaster_type')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        limit = request.args.get('limit', 50, type=int)
        
        result = disaster_service.get_all_reports(filters, limit)
        
        if result['success']:
            return jsonify({
                'reports': result['data'],
                'count': len(result['data'])
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/nearby', methods=['GET'])
def get_nearby_reports():
    """Get reports near a specific location"""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 10, type=float)
        
        if lat is None or lng is None:
            return jsonify({'error': 'lat and lng parameters are required'}), 400
        
        result = disaster_service.get_reports_by_location(lat, lng, radius)
        
        if result['success']:
            return jsonify({
                'reports': result['data'],
                'count': len(result['data']),
                'center': {'lat': lat, 'lng': lng},
                'radius_km': radius
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get all reports for statistics
        result = disaster_service.get_all_reports()
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        reports = result['data']
        
        # Calculate statistics
        stats = {
            'total_reports': len(reports),
            'pending_reports': len([r for r in reports if r['status'] == 'Pending']),
            'resolved_reports': len([r for r in reports if r['status'] == 'Resolved']),
            'critical_reports': len([r for r in reports if r['severity'] == 'Critical']),
            'disaster_types': {},
            'severity_breakdown': {
                'Low': 0,
                'Medium': 0,
                'High': 0,
                'Critical': 0
            },
            'recent_reports': reports[:5]  # Last 5 reports
        }
        
        # Count disaster types
        for report in reports:
            disaster_type = report['disaster_type']
            stats['disaster_types'][disaster_type] = stats['disaster_types'].get(disaster_type, 0) + 1
            
            # Count severity levels
            severity = report['severity']
            if severity in stats['severity_breakdown']:
                stats['severity_breakdown'][severity] += 1
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Disaster Management API',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)