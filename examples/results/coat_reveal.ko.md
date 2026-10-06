# Prompt Composer 제작 계획

실험적 지시 조합 결과입니다. 이미지·영상 생성 결과가 아닙니다.

## 프롬프트 요약

새틴 메탈 제품의 통제된 영상 제작. 피사체를 움직이지 않고 요청한 방향으로 좁은 하이라이트가 표면을 지나가게 한다. 기본 새틴 반사와 구분되는 얇은 상부 코팅 반사를 보여준다. 목표 상태에 접근한 뒤 명시한 작은 오버슈트와 줄어든 반동을 적용하고 안정시킨다. 기본 표면색과 미세결을 유지하면서 새틴 반사를 넓고 절제되게 만든다. 물리적인 면광원으로 읽을 수 있는 반사 폭과 일관된 부드러운 그림자를 만든다. 보존: 정체성, 형상, 로고, 구도, 배경.

## 상세 프롬프트

새틴 메탈 제품의 통제된 영상 제작. 피사체를 움직이지 않고 요청한 방향으로 좁은 하이라이트가 표면을 지나가게 한다. 기본 새틴 반사와 구분되는 얇은 상부 코팅 반사를 보여준다. 목표 상태에 접근한 뒤 명시한 작은 오버슈트와 줄어든 반동을 적용하고 안정시킨다. 기본 표면색과 미세결을 유지하면서 새틴 반사를 넓고 절제되게 만든다. 물리적인 면광원으로 읽을 수 있는 반사 폭과 일관된 부드러운 그림자를 만든다. 보존: 정체성, 형상, 로고, 구도, 배경. 요청 출력: 길이(초): 5; 프레임률: 24; 화면비: 16:9; 해상도: 1920x1080. 필수 조건(입력 원문): thin transparent coat; left-to-right highlight sweep; single subtle overshoot. 시간 계획: 설명한 시작 상태를 짧게 유지한다. / 요청한 주된 변화를 연속적으로 시작한다. / 주된 변화가 읽히게 하고 명시한 피사체 조건을 유지한다. / 목표 상태에 접근하고 명시한 보조 움직임만 적용한다. / 최종 상태를 유지해 검수한다.

## 선택 근거

점수는 규칙 기반 선택 점수이며 모델 성공률이 아닙니다.

- MM-007 — 방향성 스윕 전선 (60); primary_motion
- MM-024 — 스플라인 이즈·오버슈트 (45); supporting_motion_or_timing
- RS-VM-014 — Coat → 독립 상부 반사층 (60); material
- RS-VM-011 — Roughness → 하이라이트 폭·선명도 (35); material
- RS-VM-001 — Area Light 크기·형태 → 하이라이트/그림자 (32); lighting

## 시간 계획

비율은 제안한 제작 계획입니다. 실제 프레임 관측이 아닙니다.

- 0-15%: 설명한 시작 상태를 짧게 유지한다.
- 15-40%: 요청한 주된 변화를 연속적으로 시작한다.
- 40-65%: 주된 변화가 읽히게 하고 명시한 피사체 조건을 유지한다.
- 65-85%: 목표 상태에 접근하고 명시한 보조 움직임만 적용한다.
- 85-100%: 최종 상태를 유지해 검수한다.

## 필수·제외 조건(입력 원문)

```json
{
  "must_include": [
    "thin transparent coat",
    "left-to-right highlight sweep",
    "single subtle overshoot"
  ],
  "must_avoid": [
    "melt",
    "texture morph",
    "global brightness pumping"
  ]
}
```

## 출처

- [Cinema 4D Linear Field](https://help.maxon.net/c4d/2026/en-us/Content/html/FLINEAR.html)
- [Redshift Standard Material](https://help.maxon.net/c4d/en-us/Content/_REDSHIFT_/html/Standard_Material.html)
- [Cinema 4D Keys and Interpolation](https://help.maxon.net/c4d/2025/en-us/Content/html/10616.html)
- [Redshift Physical Light](https://help.maxon.net/c4d/2025/en-us/Subsystems/Default/Content/html/Physical%2BLight.html)
- [Common Redshift Light Parameters](https://help.maxon.net/c4d/2026/en-us/Content/_REDSHIFT_/html/Common%2BRedshift%2BLight%2BParameters.html)

## 미검증 사항

- 모델별 품질, 정확한 타이밍, 참조 보존은 실제 생성 비교가 필요합니다.
- 임의 요청문 전체를 자동 번역하지 않습니다. 지원하지 않는 주제는 중립적인 영문 피사체를 사용합니다.
