from django.core.management.base import BaseCommand
from products.models import Category


class Command(BaseCommand):
    help = 'Seed default cake categories'

    def handle(self, *args, **kwargs):
        categories = [
            ('Signature Cakes', 'signature-cakes', 'Unique, Handcrafted, Signature Cakes.'),
            ('Kids Cakes', 'kids-cakes', 'Fun, Colorful, Kids Cakes.'),
            ('Wedding Cakes', 'wedding-cakes', 'Elegant, Romantic, Wedding Cakes.'),
            ('Valentine Cakes', 'valentine-cakes', 'Sweet, Romantic, Valentine Cakes.'),
            ('Holiday Cakes', 'holiday-cakes', 'Festive, Flavorful, Holiday Cakes.'),
            ('Others', 'others', 'Cupcakes, Bento Cakes, and more.'),
        ]

        for name, slug, description in categories:
            obj, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': description}
            )
            self.stdout.write(
                f"{'Created' if created else 'Exists'}: {name}"
            )

        self.stdout.write(self.style.SUCCESS('\nDone. Categories seeded successfully.'))