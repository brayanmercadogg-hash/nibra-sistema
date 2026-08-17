import csv
import io
import re
from flask import Response


def export_csv(data, columns, filename):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for row in data:
        writer.writerow([row.get(c, '') if isinstance(row, dict) else getattr(row, c, '') for c in columns])
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )


def validate_password(password):
    errors = []
    if len(password) < 8:
        errors.append('Minimo 8 caracteres')
    if not re.search(r'[A-Z]', password):
        errors.append('Al menos 1 mayuscula')
    if not re.search(r'[a-z]', password):
        errors.append('Al menos 1 minuscula')
    if not re.search(r'[0-9]', password):
        errors.append('Al menos 1 numero')
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>\-_=+\[\]\\;\'`~]', password):
        errors.append('Al menos 1 caracter especial (!@#$%^&*...)')
    return errors
