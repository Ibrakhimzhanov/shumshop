-- Remove old "Старореги" placeholder product
DELETE FROM products WHERE name = 'Старореги' AND category_id = 1;

-- Add staroregi products with prices and post-purchase instructions
INSERT INTO products (category_id, name, price, description, post_purchase_info, sort_order) VALUES
(1, 'Старорег 2006-2009 (пустышка без видео)', 250000,
 'Аккаунт YouTube 2006-2009 года без видео.',
 'Kirgandan so''ng xavfsizlik bilan bog''liq barcha narsalarni o''zgartirmaslik kerak. Shubhali harakatlar uchun akkaunt bloklanishi mumkin.

Xavfsizlik ma''lumotlarini akkauntga kirgandan 7 kun o''tgach o''zgartiring, Google yangi IP/qurilmaga o''rgansin va akkaunt buzilgan deb o''ylamasin.

VPN ishlatmaslik yaxshiroq. Undan akkaunt ham bloklanishi mumkin. Yaxshi proksilar ishlating.',
 5),

(1, 'Старорег 2006-2009 (до 1000 просмотров)', 270000,
 'Аккаунт YouTube 2006-2009 года со старыми видео (до 1000 просмотров).',
 'Kirgandan so''ng xavfsizlik bilan bog''liq barcha narsalarni o''zgartirmaslik kerak. Shubhali harakatlar uchun akkaunt bloklanishi mumkin.

Xavfsizlik ma''lumotlarini akkauntga kirgandan 7 kun o''tgach o''zgartiring, Google yangi IP/qurilmaga o''rgansin va akkaunt buzilgan deb o''ylamasin.

VPN ishlatmaslik yaxshiroq. Undan akkaunt ham bloklanishi mumkin. Yaxshi proksilar ishlating.',
 6),

(1, 'Старорег 2006-2009 (1000+ просмотров)', 280000,
 'Аккаунт YouTube 2006-2009 года со старыми видео (1000+ просмотров).',
 'Kirgandan so''ng xavfsizlik bilan bog''liq barcha narsalarni o''zgartirmaslik kerak. Shubhali harakatlar uchun akkaunt bloklanishi mumkin.

Xavfsizlik ma''lumotlarini akkauntga kirgandan 7 kun o''tgach o''zgartiring, Google yangi IP/qurilmaga o''rgansin va akkaunt buzilgan deb o''ylamasin.

VPN ishlatmaslik yaxshiroq. Undan akkaunt ham bloklanishi mumkin. Yaxshi proksilar ishlating.',
 7),

(1, 'Старорег 2006-2009 с 3 функцией', 350000,
 'Аккаунт YouTube 2006-2009 года с включённой 3 функцией.',
 'Kirgandan so''ng darhol 3 funktsiyaning mavjudligini tekshiring!

3-5 kun davomida akkauntni isiting: video ko''ring, Google''da biror narsa qidiring — Google yangi qurilmaga o''rgansin. Keyin asta-sekin bezakni o''zgartirishingiz mumkin (lekin birdaniga emas — bugun nom o''zgartirdingiz, ertaga avatar va h.k.). Videolarni kamida birinchi vaqtda yashirmaslik kerak.

3 funktsiya yangilanishdan keyin juda beqaror bo''lib qoldi. Har qanday "shubhali" harakat tufayli tushib ketishi mumkin.

VPN ishlatmaslik yaxshiroq. Yaxshi proksilar ishlating.',
 8),

(1, 'Пустой канал 2026 с 3 функцией', 200000,
 'Новый пустой канал YouTube 2026 года с включённой 3 функцией.',
 'Kirgandan so''ng darhol 3 funktsiyaning mavjudligini tekshiring!

3-5 kun davomida akkauntni isiting: video ko''ring, Google''da biror narsa qidiring — Google yangi qurilmaga o''rgansin. Keyin asta-sekin bezakni o''zgartirishingiz mumkin (lekin birdaniga emas — bugun nom o''zgartirdingiz, ertaga avatar va h.k.). Videolarni kamida birinchi vaqtda yashirmaslik kerak.

3 funktsiya yangilanishdan keyin juda beqaror bo''lib qoldi. Har qanday "shubhali" harakat tufayli tushib ketishi mumkin.

VPN ishlatmaslik yaxshiroq. Yaxshi proksilar ishlating.',
 9);
