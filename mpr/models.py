from __future__ import division
from django.db import models

class Ingredient(models.Model):
    name = models.CharField(max_length=250)
    unit = models.CharField(max_length=20)

    class Meta:
        unique_together = ("name", "unit")

    def __unicode__(self):
        return self.name

class ProductManager(models.Manager):
    def search_by_ingredient(self, pattern):

        ingredients = Ingredient.objects.filter(name__icontains=pattern)

        products = set()
        for i in ingredients:
            products |= set(i.product_set.all())

        products = sorted(products, key=lambda x: x.sep)
        return products

    def search_by_product(self, pattern):

        products = Product.objects.filter(name__icontains=pattern).order_by("sep")
        return products

class Product(models.Model):
    regno = models.CharField(max_length=50, null=True)
    name = models.CharField(max_length=100)
    schedule = models.CharField(max_length=22, null=True)
    dosage_form = models.CharField(max_length=20, null=True)
    pack_size = models.FloatField(null=True)
    num_packs = models.IntegerField(null=True)
    sep = models.FloatField(null=True)
    is_generic = models.CharField(max_length=20, null=True)

    ingredients = models.ManyToManyField(Ingredient, through='ProductIngredient')

    objects = ProductManager()

    def __unicode__(self):
        return self.name

    @property
    def related_products(self):
        num_ingredients = len(self.product_ingredients.all())
        qs = Product.objects.annotate(models.Count("ingredients")).filter(ingredients__count=num_ingredients)
        for pi in self.product_ingredients.all():
            qs = qs.filter(product_ingredients__ingredient=pi.ingredient, product_ingredients__strength=pi.strength)

        return qs.order_by("sep")

    @property
    def max_fee(self):
        return self.dispensing_fee + self.sep

    @property
    def dispensing_fee(self):
        VAT = 1.14
        try:
            if self.sep < 97.06:
                return (self.sep * 0.46 + 9.25) * VAT
            elif self.sep < 258.88:
                return (self.sep * 0.33 + 22.50) * VAT
            elif self.sep < 906.10:
                return (self.sep * 0.15 + 69) * VAT
            else:
                return (self.sep * 0.05 + 160) * VAT
        except (ValueError, TypeError):
            return self.sep

    @property
    def cost_per_unit(self):
        if self.pack_size > 0:
            qty = self.pack_size * self.num_packs
        else:
            qty = self.num_packs
        return self.max_fee / qty

class ProductIngredient(models.Model):
    product = models.ForeignKey(Product, related_name="product_ingredients")
    ingredient = models.ForeignKey(Ingredient)
    strength = models.CharField(max_length=20)

    class Meta:
        unique_together = ("product", "ingredient", "strength")

    def __unicode__(self):
        return "%s %s" % (self.ingredient, self.strength)

class LastUpdated(models.Model):
    update_date = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return str(self.update_date)
