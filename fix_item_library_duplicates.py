"""
Fix ItemLibrary duplicates - ensure each combination of item_name + part_number + customer is unique
This script will scan all reports and recreate ItemLibrary with proper unique combinations
"""
from app import app, db
from models import ItemLibrary, Report

def fix_item_library():
    with app.app_context():
        print("Starting ItemLibrary cleanup...")
        
        # Step 1: Clear current ItemLibrary
        deleted_count = ItemLibrary.query.delete()
        print(f"Deleted {deleted_count} old items from ItemLibrary")
        
        # Step 2: Scan all reports and collect unique combinations
        unique_combinations = set()
        reports = Report.query.all()
        
        for report in reports:
            if report.item_name:
                # Create tuple of (item_name, part_number, customer)
                combo = (
                    report.item_name,
                    report.part_number or None,
                    report.customer or None
                )
                unique_combinations.add(combo)
        
        print(f"Found {len(unique_combinations)} unique combinations from {len(reports)} reports")
        
        # Step 3: Insert unique combinations into ItemLibrary
        added_count = 0
        for item_name, part_number, customer in sorted(unique_combinations):
            new_item = ItemLibrary(
                item_name=item_name,
                part_number=part_number,
                customer=customer
            )
            db.session.add(new_item)
            added_count += 1
        
        db.session.commit()
        print(f"Added {added_count} unique items to ItemLibrary")
        
        # Step 4: Display sample of recreated items
        print("\nSample of recreated items:")
        sample_items = ItemLibrary.query.limit(10).all()
        for item in sample_items:
            print(f"  - {item.item_name} | {item.part_number or 'No Part#'} | {item.customer or 'No Customer'}")
        
        print("\n✅ ItemLibrary cleanup completed successfully!")

if __name__ == '__main__':
    fix_item_library()
