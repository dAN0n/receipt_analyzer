package com.trpo6.receiptanalyzer;

import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.View;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }

    // Переход к активности редактирования списка продуктов
    public void addItemsWindow(View view){
        Intent intent = new Intent("productlist");
        startActivity(intent);
    }

    // Переход к активности сканирования QR-кода с чека
    public void scanQRcode(View view){
        Intent intent = new Intent("QRscanner");
        startActivity(intent);
    }
}