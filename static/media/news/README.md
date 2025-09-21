# Yangiliklar Media Fayllari

Bu papkada yangiliklar va reklamalar uchun rasm va video fayllar saqlanadi.

## Struktura

```
/static/media/news/
├── images/          # Yangiliklar uchun rasmlar
├── videos/          # Yangiliklar uchun videolar
├── thumbnails/      # Thumbnail rasmlar (auto-generated)
└── temp/           # Vaqtinchalik fayllar
```

## Fayl formatlari

### Rasmlar
- PNG, JPG, JPEG, GIF, WEBP
- Maksimal o'lchami: 5MB
- Tavsiya etilgan o'lchami: 800x600 px

### Videolar
- MP4, WEBM, MOV
- Maksimal o'lchami: 50MB
- Tavsiya etilgan davomiyligi: 30 soniya

## Fayl nomlash qoidalari

- `news_[ID]_[timestamp].[ext]` - Yangilik rasmlari uchun
- `ad_[ID]_[timestamp].[ext]` - Reklama rasmlari uchun
- `video_[ID]_[timestamp].[ext]` - Video fayllar uchun

Masalan:
- `news_1_20240115100000.jpg`
- `ad_2_20240115100000.mp4`

## Foydalanish

Media fayllar avtomatik ravishda admin paneli orqali yuklanadi va boshqariladi.