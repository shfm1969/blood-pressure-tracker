"""導出功能：PDF 和 CSV"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import pandas as pd
from datetime import datetime
from typing import List
from models.database import BloodPressureRecord


def export_to_csv(records: List[BloodPressureRecord], filename: str = None):
    """導出記錄為 CSV 檔案"""
    if filename is None:
        filename = f"血壓記錄_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    data = []
    for record in records:
        data.append({
            '日期時間': record.measured_at.strftime('%Y-%m-%d %H:%M:%S'),
            '收縮壓': record.systolic,
            '舒張壓': record.diastolic,
            '脈搏': record.pulse,
            '測量側': record.position.value if record.position else '',
            '分類': record.category or '',
            '備註': record.note or ''
        })
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    return filename


def export_to_pdf(records: List[BloodPressureRecord], filename: str = None):
    """導出記錄為 PDF 檔案"""
    if filename is None:
        filename = f"血壓記錄_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # 標題
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    title = Paragraph("血壓記錄報告", title_style)
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # 統計資訊
    if records:
        avg_systolic = sum(r.systolic for r in records) / len(records)
        avg_diastolic = sum(r.diastolic for r in records) / len(records)
        avg_pulse = sum(r.pulse for r in records) / len(records)
        
        stats_text = f"""
        <b>統計資訊：</b><br/>
        記錄筆數：{len(records)}<br/>
        平均收縮壓：{avg_systolic:.1f} mmHg<br/>
        平均舒張壓：{avg_diastolic:.1f} mmHg<br/>
        平均脈搏：{avg_pulse:.1f} bpm<br/>
        """
        stats = Paragraph(stats_text, styles['Normal'])
        story.append(stats)
        story.append(Spacer(1, 0.5*cm))
    
    # 表格資料
    table_data = [['日期時間', '收縮壓', '舒張壓', '脈搏', '測量側', '分類', '備註']]
    
    for record in records:
        table_data.append([
            record.measured_at.strftime('%Y-%m-%d\n%H:%M:%S'),
            str(record.systolic),
            str(record.diastolic),
            str(record.pulse),
            record.position.value if record.position else '',
            record.category or '',
            record.note or ''
        ])
    
    # 建立表格
    table = Table(table_data, colWidths=[3*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 2*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    story.append(table)
    
    # 建立 PDF
    doc.build(story)
    return filename

