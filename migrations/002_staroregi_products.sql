-- Create hidden subcategory for staroregi products
INSERT INTO categories (name, is_active, sort_order) VALUES
('Старореги YouTube', false, 100)
ON CONFLICT DO NOTHING;

-- Add staroregi sub-products (category_id will be set after insert)
DO $$
DECLARE
    cat_id INT;
BEGIN
    SELECT id INTO cat_id FROM categories WHERE name = 'Старореги YouTube';

    INSERT INTO products (category_id, name, price, description, post_purchase_info, sort_order) VALUES
    (cat_id, 'Пустышка без видео (2006-2009)', 250000,
     'Аккаунт YouTube 2006-2009 года без видео',
     'Kirgandan so''ng xavfsizlik bilan bog''liq barcha narsalarni o''zgartirmaslik kerak. Shubhali harakatlar uchun akkaunt bloklanishi mumkin.

Xavfsizlik ma''lumotlarini akkauntga kirgandan 7 kun o''tgach o''zgartiring, Google yangi IP/qurilmaga o''rgansin va akkaunt buzilgan deb o''ylamasin.

VPN ishlatmaslik yaxshiroq. Undan akkaunt ham bloklanishi mumkin. Yaxshi proksilar ishlating.',
     1),

    (cat_id, 'До 1000 просмотров (2006-2009)', 270000,
     'Аккаунт YouTube 2006-2009 года со старыми видео (до 1000 просмотров)',
     'Kirgandan so''ng xavfsizlik bilan bog''liq barcha narsalarni o''zgartirmaslik kerak. Shubhali harakatlar uchun akkaunt bloklanishi mumkin.

Xavfsizlik ma''lumotlarini akkauntga kirgandan 7 kun o''tgach o''zgartiring, Google yangi IP/qurilmaga o''rgansin va akkaunt buzilgan deb o''ylamasin.

VPN ishlatmaslik yaxshiroq. Undan akkaunt ham bloklanishi mumkin. Yaxshi proksilar ishlating.',
     2),

    (cat_id, '1000+ просмотров (2006-2009)', 280000,
     'Аккаунт YouTube 2006-2009 года со старыми видео (1000+ просмотров)',
     'Kirgandan so''ng xavfsizlik bilan bog''liq barcha narsalarni o''zgartirmaslik kerak. Shubhali harakatlar uchun akkaunt bloklanishi mumkin.

Xavfsizlik ma''lumotlarini akkauntga kirgandan 7 kun o''tgach o''zgartiring, Google yangi IP/qurilmaga o''rgansin va akkaunt buzilgan deb o''ylamasin.

VPN ishlatmaslik yaxshiroq. Undan akkaunt ham bloklanishi mumkin. Yaxshi proksilar ishlating.',
     3),

    (cat_id, 'С 3 функцией (2006-2009)', 350000,
     'Аккаунт YouTube 2006-2009 года с включённой 3 функцией',
     'Kirgandan so''ng darhol 3 funktsiyaning mavjudligini tekshiring!

3-5 kun davomida akkauntni isiting: video ko''ring, Google''da biror narsa qidiring — Google yangi qurilmaga o''rgansin. Keyin asta-sekin bezakni o''zgartirishingiz mumkin (lekin birdaniga emas — bugun nom o''zgartirdingiz, ertaga avatar va h.k.). Videolarni kamida birinchi vaqtda yashirmaslik kerak.

3 funktsiya yangilanishdan keyin juda beqaror bo''lib qoldi. Har qanday "shubhali" harakat tufayli tushib ketishi mumkin.

VPN ishlatmaslik yaxshiroq. Yaxshi proksilar ishlating.',
     4),

    (cat_id, 'Пустой канал 2026 с 3 функцией', 200000,
     'Новый пустой канал YouTube 2026 года с включённой 3 функцией',
     'Kirgandan so''ng darhol 3 funktsiyaning mavjudligini tekshiring!

3-5 kun davomida akkauntni isiting: video ko''ring, Google''da biror narsa qidiring — Google yangi qurilmaga o''rgansin. Keyin asta-sekin bezakni o''zgartirishingiz mumkin (lekin birdaniga emas — bugun nom o''zgartirdingiz, ertaga avatar va h.k.). Videolarni kamida birinchi vaqtda yashirmaslik kerak.

3 funktsiya yangilanishdan keyin juda beqaror bo''lib qoldi. Har qanday "shubhali" harakat tufayli tushib ketishi mumkin.

VPN ishlatmaslik yaxshiroq. Yaxshi proksilar ishlating.',
     5);
END $$;
