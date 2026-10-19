const recent_keys = [];
const konami_code = [
	'arrowup', 'arrowup',
	'arrowdown', 'arrowdown',
	'arrowleft', 'arrowright',
	'arrowleft', 'arrowright',
	'a', 'b'
];
const candy_types = ["🍬", "🍭", "🍫"];

function create_candy(x, y, scale, candy_type) {
    candy_type = candy_type % candy_types.length;

    const elem = document.createElement("span");
	elem.classList.add("animatable-candy");
	elem.innerText = candy_types[candy_type];

	document.body.appendChild(elem);

	elem.setAttribute("data-candy-scale", scale);

	elem.style.position = "absolute";
	elem.style.top = "-6rem";
	elem.style.left = `${x}dvw`;
	elem.style.zIndex = "1000";
	elem.style.userSelect = "none";
	elem.style.pointerEvents = "none";
	elem.ariaHidden = "true";

	elem.style.transform = "scale(attr(data-candy-scale type(<number>), 1))"
	return elem;
}

function candy_fall() {
	for (let i = 0; i < 100; i++) {
		const x = Math.floor(Math.random() * 100);
		const size = Math.floor(Math.random() * 18) / 10 + 1;
		const ctype = Math.floor(Math.random() * candy_types.length);
		const piece = create_candy(x, 100, size, ctype);
		const fall = piece.animate(
			[
				{transform: "translateY(0) rotate(0deg) scale(attr(data-candy-scale type(<number>), 1))"},
				{transform: "translateY(calc(100vh + 6rem)) rotate(360deg) scale(attr(data-candy-scale type(<number>), 1))"},
			],
			{duration: 3000, delay: Math.random() * 1500, easing: "ease-in"},
		);
		fall.onfinish = () => piece.remove();
	}
}

function reduced_candy_fall() {
	if (document.querySelector(".reduced-motion-candy") !== null) return;

	const candy = candy_types[Math.floor(Math.random() * candy_types.length)];

	const elem = document.createElement("span");
	elem.classList.add("reduced-motion-candy");
	elem.innerText = `${candy} You found the secret candy code!`;

	document.body.appendChild(elem);

	elem.style.position = "fixed";
	elem.style.inset = "0";
	elem.style.maxWidth = "100dvw";
	elem.style.height = "fit-content";
	elem.style.margin = "auto";
	elem.style.zIndex = "1000";
	elem.style.fontSize = "30px";
	elem.style.background = "var(--color-pastel-turq)";
	elem.style.padding = "10px";
	elem.style.border = "2px solid var(--color-black)";
	elem.style.borderRadius = "15px";
	elem.style.userSelect = "none";
	elem.style.pointerEvents = "none";
	elem.ariaHidden = "true";

	elem.style.transform = "scale(attr(data-candy-scale type(<number>), 1))"

	setTimeout(_ => {
		elem.remove();
	}, 2000);
}

function handle_keydown(event) {
	recent_keys.push(event.key.toLowerCase());
	if (recent_keys.length > konami_code.length)
		recent_keys.shift();

	const is_konami = konami_code.every((v, i, _) => {
		return v === recent_keys[i];
	});

	if (is_konami) {
		if (window.matchMedia("(prefers-reduced-motion: reduce)").matches)
			reduced_candy_fall();
		else
			candy_fall();
	}
}

function main() {
	document.addEventListener("keydown", handle_keydown);
}

document.addEventListener("DOMContentLoaded", main);