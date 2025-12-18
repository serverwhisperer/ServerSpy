"""
Excel Export module for ServerScout
Generates professional Excel reports with multiple sheets
"""

import os
import sys
import tempfile
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from datetime import datetime


def get_export_path():
    """Get export directory - use temp folder in production, exports folder in dev"""
    if getattr(sys, 'frozen', False):
        # In production, use user's temp directory
        return tempfile.gettempdir()
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')

# Export directory
EXPORT_PATH = get_export_path()


def ensure_export_directory():
    """Ensure the exports directory exists"""
    if not os.path.exists(EXPORT_PATH):
        os.makedirs(EXPORT_PATH)


def get_cell_style():
    """Return standard cell styles"""
    header_font = Font(bold=True, color='FFFFFF', size=11)
    header_fill = PatternFill(start_color='2E7D32', end_color='2E7D32', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    cell_alignment = Alignment(horizontal='left', vertical='center')
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    return {
        'header_font': header_font,
        'header_fill': header_fill,
        'header_alignment': header_alignment,
        'cell_alignment': cell_alignment,
        'border': thin_border
    }


def auto_adjust_column_width(worksheet):
    """Auto-adjust column widths based on content"""
    for column in worksheet.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        
        for cell in column:
            try:
                if cell.value:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            except:
                pass
        
        # Set width with some padding, max 50 characters
        adjusted_width = min(max_length + 2, 50)
        worksheet.column_dimensions[column_letter].width = max(adjusted_width, 10)


def create_summary_sheet(workbook, stats):
    """Create the Summary sheet"""
    ws = workbook.create_sheet("Summary", 0)
    styles = get_cell_style()
    
    # Title
    ws['A1'] = 'SERVER INVENTORY SUMMARY'
    ws['A1'].font = Font(bold=True, size=16, color='2E7D32')
    ws.merge_cells('A1:B1')
    
    # Stats table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Servers', stats.get('total', 0)],
        ['Online', stats.get('online', 0)],
        ['Offline', stats.get('offline', 0)],
        ['Not Scanned', stats.get('not_scanned', 0)],
        ['Last Scan', stats.get('last_scan', 'N/A') or 'Never'],
        ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    
    for row_idx, row_data in enumerate(summary_data, start=3):
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = styles['border']
            
            if row_idx == 3:  # Header row
                cell.font = styles['header_font']
                cell.fill = styles['header_fill']
                cell.alignment = styles['header_alignment']
            else:
                cell.alignment = styles['cell_alignment']
    
    auto_adjust_column_width(ws)


def create_inventory_sheet(workbook, servers):
    """Create the Inventory sheet with all server details"""
    ws = workbook.create_sheet("Inventory", 1)
    styles = get_cell_style()
    
    # Define columns
    columns = [
        'Hostname', 'IP', 'Domain', 'OS Type', 'Brand', 'Model', 'Serial',
        'Motherboard', 'CPU Count', 'CPU Cores', 'CPU Logical', 'CPU Model',
        'RAM Physical', 'RAM Logical (MB)', 'Disk Info', 'Network Primary',
        'OS Version', 'Service Pack', 'Status', 'Last Scan'
    ]
    
    # Write header
    for col_idx, header in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.alignment = styles['header_alignment']
        cell.border = styles['border']
    
    # Write data
    for row_idx, server in enumerate(servers, start=2):
        data = [
            server.get('hostname', ''),
            server.get('ip', ''),
            server.get('domain', ''),
            server.get('os_type', ''),
            server.get('brand', ''),
            server.get('model', ''),
            server.get('serial', ''),
            server.get('motherboard', ''),
            server.get('cpu_count', ''),
            server.get('cpu_cores', ''),
            server.get('cpu_logical_processors', ''),
            server.get('cpu_model', ''),
            server.get('ram_physical', ''),
            server.get('ram_logical', ''),
            server.get('disk_info', ''),
            server.get('network_primary', ''),
            server.get('os_version', ''),
            server.get('service_pack', ''),
            server.get('status', ''),
            server.get('last_scan', '')
        ]
        
        for col_idx, value in enumerate(data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = styles['cell_alignment']
            cell.border = styles['border']
            
            # Color coding for status
            if col_idx == 19:  # Status column
                if value == 'Online':
                    cell.fill = PatternFill(start_color='C8E6C9', end_color='C8E6C9', fill_type='solid')
                elif value == 'Offline':
                    cell.fill = PatternFill(start_color='FFCDD2', end_color='FFCDD2', fill_type='solid')
                else:
                    cell.fill = PatternFill(start_color='FFF9C4', end_color='FFF9C4', fill_type='solid')
    
    # Freeze header row
    ws.freeze_panes = 'A2'
    
    auto_adjust_column_width(ws)


def create_warnings_sheet(workbook, servers):
    """Create the Warnings sheet for servers with issues"""
    ws = workbook.create_sheet("Warnings", 2)
    styles = get_cell_style()
    
    # Define columns
    columns = ['Hostname', 'IP', 'Warning', 'Details']
    
    # Write header
    for col_idx, header in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = styles['header_font']
        cell.fill = PatternFill(start_color='D32F2F', end_color='D32F2F', fill_type='solid')
        cell.alignment = styles['header_alignment']
        cell.border = styles['border']
    
    # Collect warnings
    warnings = []
    
    for server in servers:
        # Offline servers
        if server.get('status') == 'Offline':
            warnings.append({
                'hostname': server.get('hostname', server.get('ip', 'Unknown')),
                'ip': server.get('ip', ''),
                'warning': 'Server Offline',
                'details': 'Server is not responding'
            })
        
        # Not scanned servers
        if server.get('status') == 'Not Scanned':
            warnings.append({
                'hostname': server.get('hostname', server.get('ip', 'Unknown')),
                'ip': server.get('ip', ''),
                'warning': 'Not Scanned',
                'details': 'Server has never been scanned'
            })
    
    # Write warnings
    if warnings:
        for row_idx, warning in enumerate(warnings, start=2):
            data = [
                warning['hostname'],
                warning['ip'],
                warning['warning'],
                warning['details']
            ]
            
            for col_idx, value in enumerate(data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.alignment = styles['cell_alignment']
                cell.border = styles['border']
                
                # Color coding for warning type
                if 'Offline' in warning['warning']:
                    cell.fill = PatternFill(start_color='FFCDD2', end_color='FFCDD2', fill_type='solid')
                elif 'High' in warning['warning']:
                    cell.fill = PatternFill(start_color='FFF9C4', end_color='FFF9C4', fill_type='solid')
    else:
        ws.cell(row=2, column=1, value='No warnings found').alignment = styles['cell_alignment']
    
    # Freeze header row
    ws.freeze_panes = 'A2'
    
    auto_adjust_column_width(ws)


def generate_excel_report(servers, stats):
    """
    Generate a complete Excel report
    
    Args:
        servers: list of server dictionaries
        stats: dictionary with server statistics
    
    Returns:
        str: path to generated Excel file
    """
    ensure_export_directory()
    
    # Create workbook
    wb = Workbook()
    
    # Remove default sheet
    if 'Sheet' in wb.sheetnames:
        del wb['Sheet']
    
    # Create sheets
    create_summary_sheet(wb, stats)
    create_inventory_sheet(wb, servers)
    create_warnings_sheet(wb, servers)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'inventory_{timestamp}.xlsx'
    filepath = os.path.join(EXPORT_PATH, filename)
    
    # Save workbook
    wb.save(filepath)
    
    return filepath


def get_export_filename():
    """Generate a timestamped filename for export"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'inventory_{timestamp}.xlsx'

