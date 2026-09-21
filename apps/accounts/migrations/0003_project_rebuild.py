# Rename Style -> Project, drop the ChartOfAccount/JournalEntry/JournalDetail
# double-entry ledger, and add the LetterOfCredit/LCPayment/LCLoan/Cost models,
# per the approved Accounts Module Rebuild plan.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0002_bankaccount_banktransaction_costsheet_payment_and_more'),
    ]

    operations = [
        # --- Style -> Project rename (preserves existing rows) ---
        migrations.RenameModel(old_name='Style', new_name='Project'),
        migrations.RenameField(model_name='project', old_name='style_number', new_name='project_number'),
        migrations.AlterField(
            model_name='project',
            name='buyer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='accounts.buyer'),
        ),
        migrations.AddField(
            model_name='project',
            name='currency',
            field=models.CharField(default='USD', max_length=3),
        ),
        migrations.AddField(
            model_name='project',
            name='remarks',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.RemoveField(model_name='project', name='lc_number'),
        migrations.RemoveField(model_name='project', name='lc_date'),
        migrations.RemoveField(model_name='project', name='lc_amount'),

        # --- Drop the double-entry ledger ---
        migrations.RemoveField(model_name='journaldetail', name='account'),
        migrations.RemoveField(model_name='journaldetail', name='journal_entry'),
        migrations.RemoveField(model_name='journalentry', name='created_by'),
        migrations.RemoveField(model_name='journalentry', name='reversed_entry'),
        migrations.DeleteModel(name='ChartOfAccount'),
        migrations.DeleteModel(name='JournalDetail'),
        migrations.DeleteModel(name='JournalEntry'),

        # --- New LC / Cost models ---
        migrations.CreateModel(
            name='LetterOfCredit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lc_number', models.CharField(max_length=100, unique=True)),
                ('lc_date', models.DateField()),
                ('bank_name', models.CharField(max_length=200)),
                ('lc_amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('expiry_date', models.DateField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('utilized', 'Utilized'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='active', max_length=20)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='letters_of_credit', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='letters_of_credit', to='accounts.project')),
            ],
            options={'ordering': ['-lc_date']},
        ),
        migrations.CreateModel(
            name='LCPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('bank_name', models.CharField(blank=True, max_length=200)),
                ('reference', models.CharField(blank=True, max_length=100)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lc_payments', to=settings.AUTH_USER_MODEL)),
                ('lc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lc_payments', to='accounts.letterofcredit')),
            ],
            options={'ordering': ['-payment_date']},
        ),
        migrations.CreateModel(
            name='LCLoan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loan_date', models.DateField()),
                ('bank_name', models.CharField(blank=True, max_length=200)),
                ('loan_amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('interest', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('other_charges', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('repaid_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lc_loans', to=settings.AUTH_USER_MODEL)),
                ('lc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lc_loans', to='accounts.letterofcredit')),
            ],
            options={'ordering': ['-loan_date']},
        ),
        migrations.CreateModel(
            name='Cost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cost_type', models.CharField(choices=[('fabric', 'Fabric'), ('accessories', 'Accessories'), ('production', 'Production'), ('washing', 'Washing'), ('printing', 'Printing'), ('embroidery', 'Embroidery'), ('transport', 'Transport'), ('inspection', 'Inspection'), ('lc_charges', 'LC Charges'), ('bank_charges', 'Bank Charges'), ('commission', 'Commission'), ('documentation', 'Documentation'), ('courier', 'Courier'), ('travel', 'Travel'), ('miscellaneous', 'Miscellaneous'), ('other', 'Other')], max_length=20)),
                ('cost_date', models.DateField()),
                ('description', models.CharField(blank=True, max_length=200)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('payment_status', models.CharField(choices=[('unpaid', 'Unpaid'), ('partial', 'Partially Paid'), ('paid', 'Paid')], default='unpaid', max_length=20)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='costs', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='costs', to='accounts.project')),
                ('purchase_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='costs', to='accounts.purchaseorder')),
            ],
            options={'ordering': ['-cost_date']},
        ),

        # --- SalesInvoice.lc_number -> letter_of_credit FK ---
        migrations.RemoveField(model_name='salesinvoice', name='lc_number'),
        migrations.AddField(
            model_name='salesinvoice',
            name='letter_of_credit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='accounts.letterofcredit'),
        ),
    ]
