from django.core.management.base import BaseCommand
from decimal import Decimal
from cart.models import CakeSizeMultiplier, CakeFlavorPrice, CakeCustomizationOption


class Command(BaseCommand):
    help = 'Seed default cake pricing data'

    def handle(self, *args, **kwargs):

        # ── Sizes ──────────────────────────────────────────────
        sizes = [
            ('6',  Decimal('1.00')),
            ('8',  Decimal('1.25')),
            ('10', Decimal('1.50')),
            ('12', Decimal('1.75')),
            ('14', Decimal('2.00')),
        ]
        for size, mult in sizes:
            obj, created = CakeSizeMultiplier.objects.get_or_create(
                size=size, defaults={'multiplier': mult}
            )
            self.stdout.write(f"{'Created' if created else 'Exists'}: Size {size} (x{mult})")

        # ── Flavors ────────────────────────────────────────────
        flavors = [
            ('Vanilla',    Decimal('1.00')),
            ('Chocolate',  Decimal('1.00')),
            ('Coconut',    Decimal('1.10')),
            ('Marble',     Decimal('1.10')),
            ('Fruit cake', Decimal('1.20')),
        ]
        for flavor, mult in flavors:
            obj, created = CakeFlavorPrice.objects.get_or_create(
                flavor=flavor, defaults={'price_multiplier': mult}
            )
            self.stdout.write(f"{'Created' if created else 'Exists'}: Flavor {flavor} (x{mult})")

        # ── Add-ons ────────────────────────────────────────────
        addons = [
            ('topper',        Decimal('2500.00'),  'Cake topper'),
            ('candle',        Decimal('500.00'),   'Candle'),
            ('birthday_card', Decimal('1000.00'),  'Birthday card'),
            ('chocolate',     Decimal('5000.00'),  'Chocolate box'),
            ('wine',          Decimal('15000.00'), 'Wine bottle'),
            ('whiskey',       Decimal('8000.00'),  'Whiskey 200ml'),
        ]
        for ctype, price, desc in addons:
            obj, created = CakeCustomizationOption.objects.get_or_create(
                customization_type=ctype,
                defaults={'price_per_unit': price, 'description': desc}
            )
            self.stdout.write(f"{'Created' if created else 'Exists'}: {ctype} (₦{price})")

        self.stdout.write(self.style.SUCCESS('\nDone. Cake pricing data seeded successfully.'))