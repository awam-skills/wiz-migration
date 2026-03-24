import sys
sys.path.insert(0, r'C:\Users\Administrator\.codebuddy\skills\wiz-migration\scripts')

try:
    from detector import detect_wiz_data_dir
    print('detector OK')
except Exception as e:
    print(f'detector FAILED: {e}')

try:
    from guide_generator import generate_export_guide
    print('guide_generator OK')
except Exception as e:
    print(f'guide_generator FAILED: {e}')

try:
    from migrator import run_attachment_migration
    print('migrator OK')
except Exception as e:
    print(f'migrator FAILED: {e}')

print('All imports successful!')
