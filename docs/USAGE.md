# 사용 안내

**한국어** | [English](USAGE.en.md)

## 예제를 골라 시작하기

| 예제 | 요청의 핵심 |
|---|---|
| [01 코팅 리빌](../examples/ko/01_coat_reveal.json) | 새틴 표면 위의 얇은 코팅 반사와 방향성 하이라이트 |
| [02 내부 산란](../examples/ko/02_sss_backlight.json) | 고체 형태를 유지한 채 얇은 부분에서 역광이 퍼짐 |
| [03 미세 표면 결](../examples/ko/03_micro_imperfection.json) | 회전 중 드문 미세 스크래치가 표면에 고정됨 |
| [04 랙 포커스](../examples/ko/04_rack_focus.json) | 카메라 몸체 고정, 전경에서 제품으로 초점 이동 |
| [05 안개·빛줄기](../examples/ko/05_fog_godrays.json) | 광원·매질·틈에 연결된 빛줄기 |
| [06 상대 타이밍](../examples/ko/06_curve_timing.json) | 가속·감속·오버슈트·반동·안정의 명시한 순서 |

## 내 요청 만들기

[request.json](../templates/request.json)을 복사하고 `user_brief`와 `subject.description`을 채웁니다. 빈 양식은 실제 요청이 아니므로 그대로 실행하면 입력 오류를 안내합니다.

- `visual_intent`: 재질·조명·초점·안개의 구체적인 의도.
- `motion_intent`: 움직임과 명시한 가속·감속·정착 조건.
- `subject.*_must_remain`: true로 명시한 보존 조건을 상세 프롬프트에 포함합니다.
- `constraints.must_include` / `must_avoid`: 필수·제외 조건의 문자열 목록. 원문도 결과에 보관합니다.
- `output`: 영상 길이·프레임률·화면비·해상도를 아는 경우만 입력합니다. 화면비는 `"16:9"`처럼 문자열로 지정합니다.
- `curve.curve_data`: 제공한 상대 타이밍만 사용합니다. ID만 입력하면 실제 곡선으로 해석하지 않고 unresolved 상태를 남깁니다.

지원 입력 방식은 text_only, start_only, start_end, start_middle_end, reference_video입니다. text_only 외에는 해당 자산 파일명을 지정해야 하지만 파일을 열거나 전송하지는 않습니다. 실제 생성 단계에서 사용자가 준비한 자산을 별도로 붙입니다.

이 공개판은 영상 컷 지시와 generic 어댑터만 제공합니다. 아직 모르는 재질이나 스타일은 사용자 판단과 실제 실험으로 보완해야 합니다. 한국어 전체 문장을 영어로 완전 번역하지 않으므로 정확한 자유형 영문 조건이 필요하면 영어 입력도 직접 제공합니다.

## 결과 저장

아래 경로는 실행한 현재 폴더를 기준으로 합니다. 결과에는 요청 원문이 담길 수 있어 기본적으로 Git에서 제외하는 `outputs/`에 보관합니다.

```sh
python prompt_composer.py --input examples/ko/01_coat_reveal.json --format markdown --language ko --output outputs/my-plan.ko.md
```

이미 같은 파일이 있으면 덮어쓰지 않습니다. 새 이름을 고릅니다. JSON에는 두 언어의 prompt 필드가 모두 있고, `--language`는 Markdown 표시 언어만 고릅니다.

## 검사

```sh
python validate_prompt_composer.py
python prompt_composer.py --all-fixtures
```

첫 명령은 20개 동작 검사를 실행합니다. 둘째는 12개 조립 예제와 평가를 JSON으로 출력합니다. 예제 검사가 실패하면 실패 종료 코드를 반환합니다. 결과가 맞아도 실제 생성 품질 검증으로 취급하지 않습니다.
