import peewee

db = peewee.SqliteDatabase('database.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Product(BaseModel):
    product_id = peewee.AutoField(unique=True, primary_key=True)
    price = peewee.FloatField(null=True)
    currency = peewee.CharField(max_length=12, null=True)
    name = peewee.TextField(null=True)
    description = peewee.CharField(null=True)
    ...


if __name__ == '__main__':
    with db:
        db.create_tables([Product])
