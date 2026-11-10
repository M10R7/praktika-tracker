/**
 * Нагрузочный сценарий k6 для системы «Практика-Трекер» ФИТ ЕНУ им. Л.Н. Гумилева.
 * Имитирует поведение 250 одновременных пользователей (студентов и деканата).
 *
 * Запуск: k6 run tests/load/k6_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Метрика уровня ошибок
export const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Плавный разгон до 50 VUs
    { duration: '2m', target: 250 },  // Выход на целевую нагрузку 250 VUs
    { duration: '4m', target: 250 },  // Полка стабильной нагрузки (дедлайн)
    { duration: '2m', target: 50 },   // Снижение нагрузки
    { duration: '1m', target: 0 },    // Завершение теста
  ],
  thresholds: {
    'http_req_duration': ['p(95)<300', 'p(99)<600'], // 95% запросов быстрее 300 мс (SLO)
    'errors': ['rate<0.01'],                          // Менее 1% ошибок
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

// Набор детерминированных тестовых ИИН
const TEST_IINS = [
  '030514500012',
  '030822600023',
  '031110500039',
  '030219600045',
  '030704500055',
];

export default function () {
  // 1. Просмотр главной страницы (Browse Homepage)
  let homeRes = http.get(`${BASE_URL}/`, {
    headers: { 'Accept': 'text/html' },
    tags: { name: 'Get_Home_HTML' },
  });
  check(homeRes, {
    'home status 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // 2. Проверка статуса в трекере по ИИН (Track Status)
  let randomIin = TEST_IINS[Math.floor(Math.random() * TEST_IINS.length)];
  let trackRes = http.get(`${BASE_URL}/api/v1/tracker?iin=${randomIin}`, {
    tags: { name: 'Get_Tracker_Status' },
  });
  check(trackRes, {
    'tracker status 200': (r) => r.status === 200,
    'tracker has student info': (r) => r.json().student_fullname !== undefined,
  }) || errorRate.add(1);

  sleep(2);

  // 3. Запрос каталога аккредитованных компаний (List Companies)
  let compRes = http.get(`${BASE_URL}/api/v1/companies`, {
    tags: { name: 'Get_Companies_List' },
  });
  check(compRes, {
    'companies status 200': (r) => r.status === 200,
    'companies array non-empty': (r) => Array.isArray(r.json()) && r.json().length > 0,
  }) || errorRate.add(1);

  sleep(1.5);

  // 4. Валидация БИН предприятия на лету (Validate BIN)
  let binRes = http.get(`${BASE_URL}/api/v1/validate-bin?bin=081240012740`, {
    tags: { name: 'Validate_BIN_Kaspi' },
  });
  check(binRes, {
    'bin validate status 200': (r) => r.status === 200,
    'bin is valid true': (r) => r.json().valid === true,
  }) || errorRate.add(1);

  sleep(2);
}
