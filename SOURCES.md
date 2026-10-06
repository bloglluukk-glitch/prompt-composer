# 출처와 주장 범위

**한국어** | [English](SOURCES.en.md)

확인일: 2026-10-06. Motion·Redshift 작업 지식에서 여섯 가지 사용 흐름을 선별해 공개용 카드·설정·코드로 구성했습니다. 모든 코드는 공개판의 범위에 맞춰 검수·적응했고, 임의 한국어 문장의 완전 번역이나 생성 성능을 주장하지 않습니다.

카드와 지시문은 제작자의 편집 판단입니다. Maxon의 설명문·스크린샷·장면·프로그램 파일을 묶음에 복제하지 않습니다. 공식 자료는 배경 링크로만 제공합니다. 카드에 연결한 출처는 프롬프트의 품질, 모델 성능, 정확한 렌더 값이나 제작자가 선택한 우선순위를 입증하지 않습니다.

출처 레지스트리: [sources.json](data/sources.json). 각 카드의 구성과 연결은 [knowledge.json](data/knowledge.json)에 있습니다.

| 근거 | 확인하는 배경 | 확인하지 않는 것 |
|---|---|---|
| [Linear Field](https://help.maxon.net/c4d/2026/en-us/Content/html/FLINEAR.html), [Time Effector](https://help.maxon.net/c4d/2026/en-us/Content/html/OETIME.html) | 공간별 영향과 시간에 따른 변화라는 Motion의 배경 | 빛 리빌·제품 회전 프롬프트의 생성 성공률 |
| [Keys](https://help.maxon.net/c4d/2025/en-us/Content/html/10616.html), [Time Track](https://help.maxon.net/c4d/2026/en-us/Content/html/10834.html) | 보간·상대 시간 변화의 기술적 배경 | 자연어가 정확한 F-Curve를 재현한다는 보장 |
| [Standard Material](https://help.maxon.net/c4d/en-us/Content/_REDSHIFT_/html/Standard_Material.html) | 코팅·거칠기·투과·내부 산란 등의 재질 배경 | 프롬프트가 Redshift 수치나 노드 그래프를 만든다는 주장 |
| [Physical Light](https://help.maxon.net/c4d/2025/en-us/Subsystems/Default/Content/html/Physical%2BLight.html), [Light Parameters](https://help.maxon.net/c4d/2026/en-us/Content/_REDSHIFT_/html/Common%2BRedshift%2BLight%2BParameters.html) | 광원 유형과 조명 성분의 배경 | 조합한 리빌·Rim·빛줄기의 최적성 |
| [Redshift Camera](https://help.maxon.net/c4d/en-us/Content/_REDSHIFT_/html/Redshift_Camera_Object.html) | 카메라·초점·노출의 배경 | 생성 모델이 정확한 광학을 구현한다는 보장 |
| [Standard Volume](https://help.maxon.net/c4d/2026/en-us/Content/_REDSHIFT_/html/Material%2BStandard%2BVolume.html) | 공간 매질과 산란의 배경 | 실제 생성 영상에서 빛줄기의 물리 정확성 |

문서의 버전과 노드 명칭은 달라질 수 있습니다. 이 공개판은 관찰 가능한 화면 지시를 조합하며 특정 버전의 파라미터나 C4D 장면을 출력하지 않습니다. Rim·Micro Imperfection·God Rays는 파생 개념으로 표시합니다. 공식 문서 전체를 모든 버전에서 전수 재검증한 것은 아닙니다.

제작자 [bloglluukk-glitch](https://github.com/bloglluukk-glitch)의 판단 구조와 Codex의 공개판 적응·번역 작업을 구분해 기록합니다. 선택·조립 검사는 수행했고 실제 생성·렌더 비교는 수행하지 않았습니다.
