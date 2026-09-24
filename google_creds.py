import json, base64, os, logging
logger = logging.getLogger('google_creds')
b64 = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiYm90dmVyaWZpY2F0aW9uZWxldmUiLAogICJwcml2YXRlX2tleV9pZCI6ICI3Yzc3MGQyYTQ1ZDE2MWI0NTIyOGUxZDhkNjgxNjBkODJkOTllNmQ5IiwKICAicHJpdmF0ZV9rZXkiOiAiUkVNT1ZFRCIsCiAgImNsaWVudF9lbWFpbCI6ICJpZGVudGlmaWNhdGlvbmVsZXZlQGJvdHZlcmlmaWNhdGlvbmVsZXZlLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAiY2xpZW50X2lkIjogIjExMzQ2MDQyMTExNzIzNjc1NzA1NyIsCiAgImF1dGhfdXJpIjogImh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwKICAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwKICAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsCiAgImNsaWVudF94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvaWRlbnRpZmljYXRpb25lbGV2ZSU0MGJvdHZlcmlmaWNhdGlvbmVsZXZlLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIgp9"
_BUILTIN_CREDS = json.loads(base64.b64decode(b64).decode())
def get_service_account_dict():
    for p in ['credentials.json', os.path.join(os.path.dirname(__file__), 'credentials.json')]:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                pass
    creds_env = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if creds_env:
        return json.loads(creds_env)
    return _BUILTIN_CREDS
def get_gspread_client():
    import gspread
    try:
        creds_dict = get_service_account_dict()
        if creds_dict:
            return gspread.service_account_from_dict(creds_dict)
    except Exception as e:
        logger.error(f'Error: {e}')
    return None
