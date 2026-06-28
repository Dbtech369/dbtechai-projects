import os
import sys
from datetime import datetime

def clear_screen():
    os.system('clear')

def show_header(title):
    clear_screen()
    print("=" * 50)
    print(f"  RVDoc -- {title}")
    print("=" * 50)

def diagnostic_mode():
    categories = [
        "⚙️ Landing Gear",
        "⚡ Electrical",
        "↔️ Slide-Outs",
        "❄️ Air Conditioning — Dometic, Coleman, Advent Air rooftop units",
        "💧 Plumbing",
        "🔥 Propane/Gas",
        "🔋 Generator",
        "🏕️ Awning",
        "🚿 Water Heater — Suburban, Atwood",
        "🌡️ Furnace — Suburban, Atwood",
        "🔧 Other System"
    ]
    
    while True:
        show_header("DIAGNOSTIC MODE")
        print("Select a system to diagnose:\n")
        for idx, cat in enumerate(categories, 1):
            print(f"[{idx}] {cat}")
        print("\n[B] Back to Main Menu")
        
        choice = input("\nEnter choice: ").strip().lower()
        if choice == 'b':
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(categories):
            selected = categories[int(choice) - 1]
            show_header(f"DIAGNOSTICS: {selected}")
            print(f"\n[AI Agent Placeholder]: Initializing troubleshooting loop for {selected}...")
            input("\nPress Enter to return to categories...")
        else:
            input("\nInvalid selection. Press Enter to try again...")

def pdi_mode():
    pdi_checklist = {
        "Exterior": ["Seals & Roof inspect", "Compartment doors & locks", "Running lights & Tires"],
        "Electrical": ["Shore power hookup", "Battery voltage/Converter", "12V and 120V outlets"],
        "Plumbing": ["Water pump operational", "Fresh/Waste tank valves", "Faucets, Toilet, Water Heater"],
        "Appliances": ["Furnace cycling", "Air Conditioning cooling", "Refrigerator & Microwave"],
        "LP System": ["Regulator pressure drop test", "LP Detector functional", "Gas appliances ignite"],
        "Slides & Awnings": ["Slide-out full cycle/seals", "Awning extend/retract & lights"],
        "Chassis/Hitch": ["Landing gear / Jacks / Auto level", "Kingpin/Coupler & safety chains"],
        "Interior": ["All lights & ceiling fans", "Windows, doors, and cabinet latches"]
    }
    
    show_header("PDI MODE (Pre-Delivery Inspection)")
    print("Starting a new guided inspection report...\n")
    report = {}
    
    for section, items in pdi_checklist.items():
        show_header(f"PDI: {section.upper()}")
        report[section] = {}
        
        for item in items:
            while True:
                print(f"\n🔹 Check: {item}")
                status = input("Pass (P) / Fail (F) / Skip (S): ").strip().lower()
                if status in ['p', 'f', 's']:
                    mapping = {'p': 'PASS ✅', 'f': 'FAIL ❌', 's': 'SKIPPED 🟡'}
                    report[section][item] = mapping[status]
                    break
                print("Invalid input. Use P, F, or S.")
                
    show_header("INSPECTION COMPLETE")
    print("Generating PDI Report Summary:\n")
    for section, results in report.items():
        print(f"--- {section} ---")
        for item, res in results.items():
            print(f"  {res} : {item}")
            
    # REAL FILE SAVING LOGIC ACCESSED HERE
    os.makedirs('reports', exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"reports/PDI_Report_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"=== RVDoc PDI REPORT: {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n\n")
        for section, results in report.items():
            f.write(f"--- {section.upper()} ---\n")
            for item, res in results.items():
                f.write(f"  {res} : {item}\n")
            f.write("\n")
            
    print(f"\n💾 Report safely stored in: {filename}")
    input("\nPress Enter to return to Main Menu...")

def main_menu():
    while True:
        show_header("MAIN MENU")
        print("Select operational mode:\n")
        print("[1] 🔧 Diagnostic Mode (Symptom Troubleshooting)")
        print("[2] ✅ PDI Mode (Guided Pre-Delivery Inspection)")
        print("[Q] Quit Application")
        
        choice = input("\nSelect an option: ").strip().lower()
        if choice == '1':
            diagnostic_mode()
        elif choice == '2':
            pdi_mode()
        elif choice == 'q':
            clear_screen()
            print("Exiting RVDoc. Work hard, tech safe.")
            sys.exit()
        else:
            input("\nInvalid option. Press Enter to retry...")

if __name__ == "__main__":
    main_menu()
